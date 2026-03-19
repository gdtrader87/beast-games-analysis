"""
BeastBet Live - Market Intelligence & Analysis

Advanced market analysis for prediction markets including:
- Predictive odds vs actual outcomes
- Volatility analysis
- Bettor sentiment tracking
- Optimal timing for placing bets
- Market efficiency metrics

Production-grade implementation with comprehensive statistical analysis.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
import statistics
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class OddsSnapshot:
    """Point-in-time snapshot of odds for analysis."""
    contestant_id: str
    contestant_name: str
    odds: Decimal
    timestamp: datetime
    bet_count: int
    volume: Decimal


@dataclass
class PredictionResult:
    """Result of a prediction with confidence metrics."""
    contestant_id: str
    contestant_name: str
    predicted_winner: bool
    confidence: float  # 0-1
    odds_at_prediction: Decimal
    implied_probability: Decimal
    timestamp: datetime
    actual_outcome: Optional[bool] = None
    correct: Optional[bool] = None


@dataclass
class VolatilityMetric:
    """Volatility analysis for a contestant's odds."""
    contestant_id: str
    contestant_name: str
    mean_odds: Decimal
    std_dev: Decimal
    volatility_score: float  # 0-100
    price_movement: Decimal  # Latest - first
    time_period: str


class MarketAnalyzer:
    """
    Advanced market analysis engine for prediction markets.
    
    Provides real-time analysis, predictive capabilities, sentiment tracking,
    and optimal timing recommendations.
    """
    
    def __init__(self):
        """Initialize the market analyzer."""
        self.odds_history: Dict[str, List[OddsSnapshot]] = {}
        self.predictions: List[PredictionResult] = []
        self.bettor_sentiment: Dict[str, List[float]] = {}  # user_id -> sentiment scores
        self.market_efficiency_scores: List[float] = []
        
        logger.info("Market analyzer initialized")
    
    def record_odds_snapshot(self, contestant_id: str, contestant_name: str,
                            odds: Decimal, bet_count: int, volume: Decimal) -> None:
        """
        Record a point-in-time snapshot of odds for historical analysis.
        
        Args:
            contestant_id: Contestant identifier
            contestant_name: Contestant name
            odds: Current odds
            bet_count: Number of bets on this contestant
            volume: Total volume bet on this contestant
        """
        if contestant_id not in self.odds_history:
            self.odds_history[contestant_id] = []
        
        snapshot = OddsSnapshot(
            contestant_id=contestant_id,
            contestant_name=contestant_name,
            odds=odds,
            timestamp=datetime.utcnow(),
            bet_count=bet_count,
            volume=volume
        )
        
        self.odds_history[contestant_id].append(snapshot)
        logger.debug(f"Recorded odds snapshot for {contestant_name}: {odds}")
    
    def get_odds_history(self, contestant_id: str, 
                        time_minutes: int = 60) -> List[OddsSnapshot]:
        """
        Get odds history for a contestant within a time window.
        
        Args:
            contestant_id: Target contestant
            time_minutes: Look-back window in minutes
            
        Returns:
            List of recent odds snapshots
        """
        if contestant_id not in self.odds_history:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_minutes)
        return [
            snapshot for snapshot in self.odds_history[contestant_id]
            if snapshot.timestamp >= cutoff_time
        ]
    
    def calculate_volatility(self, contestant_id: str,
                            time_minutes: int = 60) -> Optional[VolatilityMetric]:
        """
        Calculate odds volatility for a contestant.
        
        Higher volatility indicates less stable odds (more uncertainty).
        
        Args:
            contestant_id: Target contestant
            time_minutes: Analysis window in minutes
            
        Returns:
            VolatilityMetric with statistical measures
        """
        snapshots = self.get_odds_history(contestant_id, time_minutes)
        
        if len(snapshots) < 2:
            logger.warning(f"Insufficient data for volatility calc on {contestant_id}")
            return None
        
        odds_values = [float(s.odds) for s in snapshots]
        
        # Calculate statistics
        mean_odds = Decimal(str(statistics.mean(odds_values)))
        std_dev = Decimal(str(statistics.stdev(odds_values))) if len(odds_values) > 1 else Decimal("0")
        
        # Volatility score: normalized to 0-100
        # Higher std_dev relative to mean = higher volatility
        coefficient_of_variation = float(std_dev / mean_odds) if mean_odds > 0 else 0
        volatility_score = min(coefficient_of_variation * 100, 100)
        
        # Price movement
        price_movement = snapshots[-1].odds - snapshots[0].odds
        
        return VolatilityMetric(
            contestant_id=contestant_id,
            contestant_name=snapshots[0].contestant_name,
            mean_odds=mean_odds,
            std_dev=std_dev,
            volatility_score=volatility_score,
            price_movement=price_movement,
            time_period=f"Last {time_minutes} min"
        )
    
    def predict_winner(self, contestant_odds: Dict[str, Decimal],
                      market_efficiency: float = 0.8) -> List[PredictionResult]:
        """
        Predict likely winner based on implied probabilities.
        
        Accounts for market efficiency (how well odds reflect reality).
        
        Args:
            contestant_odds: Dict of contestant_id -> odds
            market_efficiency: 0-1, how efficient the market is at pricing (0.8 = 80%)
            
        Returns:
            List of predictions sorted by confidence
        """
        predictions = []
        
        # Calculate implied probabilities
        total_probability = Decimal("0")
        implied_probs = {}
        
        for contestant_id, odds in contestant_odds.items():
            implied_prob = Decimal("1") / odds
            implied_probs[contestant_id] = implied_prob
            total_probability += implied_prob
        
        # Normalize (account for juice/overround)
        for contestant_id in implied_probs:
            implied_probs[contestant_id] = implied_probs[contestant_id] / total_probability
        
        # Generate predictions
        for contestant_id, odds in contestant_odds.items():
            implied_prob = implied_probs[contestant_id]
            
            # Confidence: how likely this contestant is to win
            confidence = float(implied_prob)
            
            # Predicted winner: if prob > average
            avg_prob = Decimal("1") / Decimal(str(len(contestant_odds)))
            predicted_winner = implied_prob > avg_prob
            
            prediction = PredictionResult(
                contestant_id=contestant_id,
                contestant_name=f"Contestant_{contestant_id}",
                predicted_winner=predicted_winner,
                confidence=confidence,
                odds_at_prediction=odds,
                implied_probability=implied_prob,
                timestamp=datetime.utcnow()
            )
            
            predictions.append(prediction)
        
        # Sort by confidence (descending)
        predictions.sort(key=lambda p: p.confidence, reverse=True)
        
        return predictions
    
    def analyze_bettor_sentiment(self, user_id: str,
                                recent_bets: List) -> float:
        """
        Analyze a bettor's sentiment based on recent performance.
        
        Sentiment = (recent_wins / total_recent_bets) * 100
        
        Args:
            user_id: Target user
            recent_bets: List of recent bets
            
        Returns:
            Sentiment score 0-100 (higher = more bullish/confident)
        """
        if not recent_bets:
            return 0.0
        
        from beastbet_core import BetOutcome
        
        wins = len([b for b in recent_bets if b.status == BetOutcome.WON])
        sentiment = (wins / len(recent_bets)) * 100
        
        if user_id not in self.bettor_sentiment:
            self.bettor_sentiment[user_id] = []
        
        self.bettor_sentiment[user_id].append(sentiment)
        
        # Keep only last 100 sentiment readings
        if len(self.bettor_sentiment[user_id]) > 100:
            self.bettor_sentiment[user_id] = self.bettor_sentiment[user_id][-100:]
        
        logger.debug(f"Bettor {user_id} sentiment: {sentiment:.1f}%")
        return sentiment
    
    def get_optimal_betting_time(self, contestant_id: str,
                                time_minutes: int = 60) -> Optional[Tuple[str, float]]:
        """
        Determine optimal time to place a bet based on odds movement.
        
        Algorithm:
        - If odds increasing (good for bettor): recommend betting soon
        - If odds stable: recommend betting at any time
        - If odds decreasing: recommend waiting for bounce
        
        Args:
            contestant_id: Target contestant
            time_minutes: Look-back period
            
        Returns:
            Tuple of (recommendation, confidence) or None if insufficient data
        """
        snapshots = self.get_odds_history(contestant_id, time_minutes)
        
        if len(snapshots) < 3:
            return None
        
        # Analyze trend
        recent_odds = [float(s.odds) for s in snapshots[-10:]]
        
        if len(recent_odds) < 2:
            return None
        
        # Calculate moving average
        short_ma = statistics.mean(recent_odds[-3:]) if len(recent_odds) >= 3 else recent_odds[-1]
        long_ma = statistics.mean(recent_odds)
        
        # Calculate volatility
        volatility = statistics.stdev(recent_odds) if len(recent_odds) > 1 else 0
        
        # Determine trend
        trend_direction = short_ma - long_ma
        
        if trend_direction > 0:
            recommendation = "BET_NOW"  # Odds rising, favorable
            confidence = min(abs(trend_direction) / (long_ma * 0.1), 1.0)
        elif trend_direction < -0.05:
            recommendation = "WAIT"  # Odds falling, unfavorable
            confidence = min(abs(trend_direction) / (long_ma * 0.1), 1.0)
        else:
            recommendation = "STABLE"  # Stable odds
            confidence = 0.5
        
        logger.info(f"Timing recommendation for {contestant_id}: {recommendation} (confidence: {confidence:.2f})")
        
        return (recommendation, confidence)
    
    def calculate_market_efficiency(self, market_data: Dict) -> float:
        """
        Calculate overall market efficiency score.
        
        Efficiency measures how well the market prices reflect reality:
        - High efficiency: odds reflect true probabilities
        - Low efficiency: potential arbitrage opportunities
        
        Factors considered:
        - Overround (sum of implied probabilities)
        - Odds consistency
        - Bet volume concentration
        
        Args:
            market_data: Market summary data
            
        Returns:
            Efficiency score 0-1 (closer to 1 = more efficient)
        """
        if not market_data.get('contestants'):
            return 0.5
        
        # Calculate overround
        total_probability = Decimal("0")
        for contestant in market_data['contestants']:
            total_probability += Decimal("1") / Decimal(str(contestant['odds']))
        
        overround = float(total_probability)
        
        # Expected overround for fair market: ~1.02-1.05 (2-5% juice)
        # Calculate deviation
        expected_overround = 1.03
        overround_deviation = abs(overround - expected_overround) / expected_overround
        
        # Volume concentration (lower = more distributed = more efficient)
        volumes = [float(c['total_volume']) for c in market_data['contestants']]
        total_volume = sum(volumes)
        
        if total_volume == 0:
            concentration = 0.5
        else:
            concentration = max(volumes) / total_volume
        
        # Efficiency = 1 - penalties
        efficiency = 1.0 - (overround_deviation * 0.3 + (concentration - 0.2) * 0.3)
        efficiency = max(0.0, min(1.0, efficiency))
        
        self.market_efficiency_scores.append(efficiency)
        
        logger.info(f"Market efficiency: {efficiency:.2%}")
        
        return efficiency
    
    def generate_analysis_report(self, market_data: Dict,
                                market_object) -> Dict:
        """
        Generate comprehensive market analysis report.
        
        Args:
            market_data: Market summary
            market_object: PredictionMarket instance
            
        Returns:
            Detailed analysis report
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "market_id": market_data.get('market_id'),
            "market_name": market_data.get('market_name'),
            "efficiency": self.calculate_market_efficiency(market_data),
            "volatility_analysis": [],
            "predictions": [],
            "timing_recommendations": {},
            "sentiment_analysis": {},
            "summary": {}
        }
        
        # Volatility analysis per contestant
        for contestant in market_data.get('contestants', []):
            vol_metric = self.calculate_volatility(contestant['id'])
            if vol_metric:
                report["volatility_analysis"].append({
                    "contestant": contestant['name'],
                    "volatility_score": vol_metric.volatility_score,
                    "mean_odds": float(vol_metric.mean_odds),
                    "std_dev": float(vol_metric.std_dev),
                    "price_movement": float(vol_metric.price_movement)
                })
        
        # Predictions
        contestant_odds = {
            c['id']: Decimal(str(c['odds']))
            for c in market_data.get('contestants', [])
        }
        
        if contestant_odds:
            predictions = self.predict_winner(contestant_odds)
            report["predictions"] = [
                {
                    "contestant": p.contestant_name,
                    "confidence": p.confidence,
                    "implied_probability": float(p.implied_probability),
                    "odds": float(p.odds_at_prediction)
                }
                for p in predictions
            ]
        
        # Timing recommendations
        for contestant in market_data.get('contestants', []):
            timing = self.get_optimal_betting_time(contestant['id'])
            if timing:
                report["timing_recommendations"][contestant['name']] = {
                    "recommendation": timing[0],
                    "confidence": timing[1]
                }
        
        # Sentiment analysis
        for user_id, portfolio in market_object.user_portfolios.items():
            recent_bets = market_object.get_user_bets(user_id)[:10]
            sentiment = self.analyze_bettor_sentiment(user_id, recent_bets)
            report["sentiment_analysis"][user_id] = {
                "sentiment_score": sentiment,
                "interpretation": self._interpret_sentiment(sentiment),
                "recent_bets_analyzed": len(recent_bets)
            }
        
        # Summary insights
        report["summary"] = {
            "high_volatility_contestants": len([
                v for v in report["volatility_analysis"]
                if v["volatility_score"] > 50
            ]),
            "average_efficiency": float(statistics.mean(
                self.market_efficiency_scores[-10:]
            )) if self.market_efficiency_scores else 0,
            "total_predictions": len(report["predictions"]),
            "traders_analyzed": len(report["sentiment_analysis"])
        }
        
        logger.info("Market analysis report generated")
        
        return report
    
    def _interpret_sentiment(self, sentiment_score: float) -> str:
        """Interpret sentiment score as human-readable text."""
        if sentiment_score >= 75:
            return "Extremely Bullish"
        elif sentiment_score >= 60:
            return "Bullish"
        elif sentiment_score >= 40:
            return "Neutral"
        elif sentiment_score >= 25:
            return "Bearish"
        else:
            return "Extremely Bearish"
    
    def export_analysis(self) -> str:
        """Export analysis data as JSON."""
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "odds_history_entries": sum(len(v) for v in self.odds_history.values()),
            "predictions_count": len(self.predictions),
            "bettor_sentiment_users": len(self.bettor_sentiment),
            "market_efficiency_readings": len(self.market_efficiency_scores),
            "avg_efficiency": float(statistics.mean(self.market_efficiency_scores)) if self.market_efficiency_scores else 0
        }, indent=2)


class PredictiveOddsModel:
    """
    ML-ready predictive model for odds movement.
    
    Can be trained on historical odds data to predict future movements.
    """
    
    def __init__(self):
        """Initialize predictive model."""
        self.training_data = []
        self.model_performance = []
        
        logger.info("Predictive odds model initialized")
    
    def add_training_example(self, historical_odds: List[Decimal],
                            actual_outcome: bool) -> None:
        """
        Add training example to the model.
        
        Args:
            historical_odds: Sequence of odds leading to outcome
            actual_outcome: Whether prediction was correct
        """
        self.training_data.append({
            "odds_sequence": [float(o) for o in historical_odds],
            "outcome": actual_outcome,
            "timestamp": datetime.utcnow()
        })
    
    def predict_odds_movement(self, recent_odds: List[Decimal],
                             time_horizon_seconds: int = 300) -> Tuple[str, float]:
        """
        Predict odds movement direction for next time period.
        
        Args:
            recent_odds: Recent odds sequence
            time_horizon_seconds: Prediction window
            
        Returns:
            Tuple of (direction: UP/DOWN/STABLE, confidence: 0-1)
        """
        if len(recent_odds) < 3:
            return ("STABLE", 0.5)
        
        odds_floats = [float(o) for o in recent_odds]
        
        # Simple trend analysis
        recent_avg = statistics.mean(odds_floats[-5:])
        older_avg = statistics.mean(odds_floats[:5]) if len(odds_floats) >= 10 else statistics.mean(odds_floats[:len(odds_floats)//2])
        
        trend = recent_avg - older_avg
        
        if trend > 0.02:
            return ("UP", min(trend / 0.1, 1.0))
        elif trend < -0.02:
            return ("DOWN", min(abs(trend) / 0.1, 1.0))
        else:
            return ("STABLE", 0.5)
    
    def get_model_accuracy(self) -> float:
        """Calculate model accuracy on training data."""
        if not self.model_performance:
            return 0.0
        
        correct = len([x for x in self.model_performance if x])
        return correct / len(self.model_performance)


if __name__ == "__main__":
    print("=== BeastBet Live Market Analysis Demo ===\n")
    
    analyzer = MarketAnalyzer()
    
    # Record some sample odds snapshots
    print("Recording odds snapshots...")
    for i in range(5):
        analyzer.record_odds_snapshot(
            "contestant_1",
            "Alpha",
            Decimal("4.50") + Decimal(str(i * 0.1)),
            10 + i,
            Decimal("500") + Decimal(str(i * 50))
        )
    
    # Calculate volatility
    volatility = analyzer.calculate_volatility("contestant_1")
    if volatility:
        print(f"\nVolatility Analysis:")
        print(f"  Mean Odds: {volatility.mean_odds}")
        print(f"  Std Dev: {volatility.std_dev}")
        print(f"  Volatility Score: {volatility.volatility_score:.2f}/100")
        print(f"  Price Movement: {volatility.price_movement}")
    
    # Predict winner
    contestant_odds = {
        "contestant_1": Decimal("4.50"),
        "contestant_2": Decimal("3.00"),
        "contestant_3": Decimal("5.00")
    }
    
    predictions = analyzer.predict_winner(contestant_odds)
    print(f"\nWinner Predictions:")
    for pred in predictions:
        print(f"  {pred.contestant_id}: {pred.confidence:.1%} confidence")
    
    print(f"\nAnalyzer state: {analyzer.export_analysis()}")
