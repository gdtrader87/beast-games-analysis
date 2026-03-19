"""
BeastBet Live - Core Prediction Market Engine

This module provides the core prediction market functionality for Beast Games,
including real-time odds calculation, betting simulation, settlement logic,
and revenue tracking with 5% platform rake.

Production-grade implementation with comprehensive error handling and logging.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
import uuid
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BetOutcome(Enum):
    """Possible outcomes for a bet."""
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"
    VOIDED = "voided"


class OrderStatus(Enum):
    """Status of a placed order."""
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class Contestant:
    """Represents a contestant in the Beast Games competition."""
    id: str
    name: str
    initial_win_probability: float = 0.20
    current_odds: Decimal = Decimal("4.00")
    total_volume: Decimal = Decimal("0")
    bets_placed: int = 0
    
    def __post_init__(self):
        """Validate contestant data."""
        if not 0 < self.initial_win_probability < 1:
            raise ValueError(f"Win probability must be between 0 and 1, got {self.initial_win_probability}")
        if self.current_odds <= Decimal("1"):
            raise ValueError(f"Odds must be > 1, got {self.current_odds}")


@dataclass
class Bet:
    """Represents a single bet placed by a user."""
    id: str
    user_id: str
    contestant_id: str
    amount: Decimal
    odds_at_placement: Decimal
    timestamp: datetime
    status: BetOutcome = BetOutcome.PENDING
    payout: Decimal = Decimal("0")
    roi: Decimal = Decimal("0")
    
    def calculate_payout(self) -> Decimal:
        """Calculate potential payout for this bet."""
        if self.status == BetOutcome.WON:
            self.payout = self.amount * self.odds_at_placement
            self.roi = ((self.payout - self.amount) / self.amount) * 100
            return self.payout
        elif self.status in [BetOutcome.CANCELLED, BetOutcome.VOIDED]:
            self.payout = self.amount
            self.roi = Decimal("0")
            return self.amount
        else:
            self.payout = Decimal("0")
            self.roi = Decimal("-100")
            return Decimal("0")


@dataclass
class Order:
    """Represents a market order for multiple bets."""
    id: str
    user_id: str
    contestant_id: str
    original_amount: Decimal
    remaining_amount: Decimal
    odds_target: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.OPEN
    bets_created: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserPortfolio:
    """Tracks a user's betting portfolio and performance."""
    user_id: str
    total_wagered: Decimal = Decimal("0")
    total_won: Decimal = Decimal("0")
    total_lost: Decimal = Decimal("0")
    open_bets_count: int = 0
    roi_percentage: Decimal = Decimal("0")
    referral_count: int = 0
    
    def update_metrics(self, won: Decimal, lost: Decimal):
        """Update portfolio metrics after settlement."""
        self.total_won += won
        self.total_lost += lost
        if self.total_wagered > 0:
            self.roi_percentage = ((self.total_won - self.total_lost) / self.total_wagered) * 100


class PredictionMarket:
    """
    Core prediction market engine for BeastBet Live.
    
    Manages competitions, contestants, betting orders, odds calculation,
    and settlement with revenue tracking.
    """
    
    PLATFORM_RAKE = Decimal("0.05")  # 5% platform commission
    MIN_BET = Decimal("1.00")
    MAX_BET = Decimal("10000.00")
    
    def __init__(self, competition_id: str, market_name: str):
        """
        Initialize a prediction market for a competition.
        
        Args:
            competition_id: Unique identifier for the competition
            market_name: Human-readable name for the market
        """
        self.competition_id = competition_id
        self.market_name = market_name
        self.created_at = datetime.utcnow()
        self.is_active = True
        
        # Storage
        self.contestants: Dict[str, Contestant] = {}
        self.bets: Dict[str, Bet] = {}
        self.orders: Dict[str, Order] = {}
        self.user_portfolios: Dict[str, UserPortfolio] = {}
        
        # Revenue tracking
        self.total_volume = Decimal("0")
        self.total_rake_collected = Decimal("0")
        self.total_payouts = Decimal("0")
        
        logger.info(f"Market created: {market_name} ({competition_id})")
    
    def add_contestant(self, name: str, win_probability: Optional[float] = None) -> Contestant:
        """
        Add a contestant to the competition.
        
        Args:
            name: Contestant's name
            win_probability: Expected win probability (default: equal split)
            
        Returns:
            Created Contestant instance
        """
        if len(self.contestants) >= 5:
            raise ValueError("Maximum 5 contestants per market")
        
        contestant_id = str(uuid.uuid4())[:8]
        
        # Default probability split evenly if not provided
        if win_probability is None:
            win_probability = 1.0 / (6 - len(self.contestants))  # Account for this new one
        
        # Convert probability to decimal odds: odds = 1 / probability
        odds = Decimal("1") / Decimal(str(win_probability))
        
        contestant = Contestant(
            id=contestant_id,
            name=name,
            initial_win_probability=win_probability,
            current_odds=odds
        )
        
        self.contestants[contestant_id] = contestant
        logger.info(f"Added contestant: {name} ({contestant_id}) - Odds: {odds}")
        
        return contestant
    
    def get_contestant(self, contestant_id: str) -> Optional[Contestant]:
        """Retrieve a contestant by ID."""
        return self.contestants.get(contestant_id)
    
    def place_bet(self, user_id: str, contestant_id: str, amount: Decimal) -> Bet:
        """
        Place a bet on a contestant.
        
        Args:
            user_id: Unique identifier for the user
            contestant_id: Target contestant
            amount: Bet amount in currency units
            
        Returns:
            Created Bet instance
            
        Raises:
            ValueError: If bet parameters are invalid
        """
        if amount < self.MIN_BET or amount > self.MAX_BET:
            raise ValueError(f"Bet amount must be between {self.MIN_BET} and {self.MAX_BET}")
        
        if contestant_id not in self.contestants:
            raise ValueError(f"Contestant {contestant_id} not found")
        
        if not self.is_active:
            raise ValueError("Market is closed")
        
        contestant = self.contestants[contestant_id]
        
        # Create bet
        bet_id = str(uuid.uuid4())[:8]
        bet = Bet(
            id=bet_id,
            user_id=user_id,
            contestant_id=contestant_id,
            amount=Decimal(str(amount)),
            odds_at_placement=contestant.current_odds,
            timestamp=datetime.utcnow()
        )
        
        self.bets[bet_id] = bet
        
        # Update contestant volume
        contestant.total_volume += Decimal(str(amount))
        contestant.bets_placed += 1
        
        # Update market volume
        self.total_volume += Decimal(str(amount))
        
        # Update user portfolio
        if user_id not in self.user_portfolios:
            self.user_portfolios[user_id] = UserPortfolio(user_id)
        
        portfolio = self.user_portfolios[user_id]
        portfolio.total_wagered += Decimal(str(amount))
        portfolio.open_bets_count += 1
        
        logger.info(f"Bet placed: {user_id} bet ${amount} on {contestant.name} @ {bet.odds_at_placement}")
        
        return bet
    
    def create_order(self, user_id: str, contestant_id: str, amount: Decimal,
                    odds_target: Optional[Decimal] = None) -> Order:
        """
        Create a market order for multiple partial fills.
        
        Args:
            user_id: User placing the order
            contestant_id: Target contestant
            amount: Total amount to allocate
            odds_target: Minimum odds acceptable (optional)
            
        Returns:
            Created Order instance
        """
        if contestant_id not in self.contestants:
            raise ValueError(f"Contestant {contestant_id} not found")
        
        order_id = str(uuid.uuid4())[:8]
        order = Order(
            id=order_id,
            user_id=user_id,
            contestant_id=contestant_id,
            original_amount=Decimal(str(amount)),
            remaining_amount=Decimal(str(amount)),
            odds_target=odds_target
        )
        
        self.orders[order_id] = order
        logger.info(f"Order created: {order_id} - {user_id} orders ${amount} on {contestant_id}")
        
        return order
    
    def fill_order(self, order_id: str, fill_amount: Decimal) -> Bet:
        """
        Fill part or all of a market order by creating a bet.
        
        Args:
            order_id: Target order ID
            fill_amount: Amount to fill
            
        Returns:
            Created Bet instance
        """
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self.orders[order_id]
        
        if fill_amount > order.remaining_amount:
            raise ValueError(f"Cannot fill {fill_amount}, only {order.remaining_amount} remaining")
        
        # Check odds if target was set
        contestant = self.contestants[order.contestant_id]
        if order.odds_target and contestant.current_odds < order.odds_target:
            raise ValueError(f"Current odds {contestant.current_odds} below target {order.odds_target}")
        
        # Create bet from order
        bet = self.place_bet(order.user_id, order.contestant_id, fill_amount)
        
        order.bets_created.append(bet.id)
        order.remaining_amount -= fill_amount
        
        if order.remaining_amount == 0:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED
        
        return bet
    
    def update_odds(self, contestant_id: str, new_odds: Decimal) -> None:
        """
        Update odds for a contestant (typically based on external data or bets).
        
        Args:
            contestant_id: Target contestant
            new_odds: New odds value
        """
        if contestant_id not in self.contestants:
            raise ValueError(f"Contestant {contestant_id} not found")
        
        if new_odds <= Decimal("1"):
            raise ValueError("Odds must be > 1")
        
        contestant = self.contestants[contestant_id]
        old_odds = contestant.current_odds
        contestant.current_odds = new_odds
        
        logger.info(f"Odds updated: {contestant.name} {old_odds} -> {new_odds}")
    
    def settle_bet(self, bet_id: str, won: bool) -> Decimal:
        """
        Settle a bet (mark as won or lost).
        
        Args:
            bet_id: Target bet ID
            won: Whether the bet won
            
        Returns:
            Amount paid out (0 if lost, payout if won, refund if voided)
        """
        if bet_id not in self.bets:
            raise ValueError(f"Bet {bet_id} not found")
        
        bet = self.bets[bet_id]
        
        if bet.status != BetOutcome.PENDING:
            raise ValueError(f"Bet {bet_id} already settled as {bet.status.value}")
        
        user = self.user_portfolios[bet.user_id]
        
        if won:
            bet.status = BetOutcome.WON
            payout = bet.calculate_payout()
            
            # Deduct rake from payout
            rake = payout * self.PLATFORM_RAKE
            net_payout = payout - rake
            
            self.total_rake_collected += rake
            self.total_payouts += net_payout
            user.total_won += net_payout
            
            logger.info(f"Bet settled (WIN): {bet_id} - Payout: ${payout}, Rake: ${rake}")
        else:
            bet.status = BetOutcome.LOST
            user.total_lost += bet.amount
            logger.info(f"Bet settled (LOSS): {bet_id} - Amount: ${bet.amount}")
        
        user.open_bets_count -= 1
        user.update_metrics(user.total_won, user.total_lost)
        
        return bet.calculate_payout()
    
    def void_bets(self, contestant_id: str) -> Tuple[int, Decimal]:
        """
        Void all bets on a contestant (e.g., if contestant is disqualified).
        
        Args:
            contestant_id: Target contestant
            
        Returns:
            Tuple of (number of bets voided, total refunded)
        """
        voided_count = 0
        total_refunded = Decimal("0")
        
        for bet_id, bet in list(self.bets.items()):
            if bet.contestant_id == contestant_id and bet.status == BetOutcome.PENDING:
                bet.status = BetOutcome.VOIDED
                total_refunded += bet.amount
                voided_count += 1
                
                user = self.user_portfolios[bet.user_id]
                user.open_bets_count -= 1
        
        logger.info(f"Voided {voided_count} bets on {contestant_id}, refunded ${total_refunded}")
        
        return voided_count, total_refunded
    
    def calculate_implied_probability(self, contestant_id: str) -> Decimal:
        """Calculate implied probability from current odds."""
        if contestant_id not in self.contestants:
            raise ValueError(f"Contestant {contestant_id} not found")
        
        odds = self.contestants[contestant_id].current_odds
        return Decimal("1") / odds
    
    def get_market_summary(self) -> Dict:
        """
        Get a comprehensive market summary.
        
        Returns:
            Dictionary containing market statistics and state
        """
        total_open_bets = sum(
            1 for bet in self.bets.values()
            if bet.status == BetOutcome.PENDING
        )
        
        contestants_data = []
        for c_id, contestant in self.contestants.items():
            implied_prob = self.calculate_implied_probability(c_id)
            contestants_data.append({
                "id": c_id,
                "name": contestant.name,
                "odds": float(contestant.current_odds),
                "implied_probability": float(implied_prob),
                "total_volume": float(contestant.total_volume),
                "bets_placed": contestant.bets_placed
            })
        
        return {
            "market_id": self.competition_id,
            "market_name": self.market_name,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "total_volume": float(self.total_volume),
            "total_rake_collected": float(self.total_rake_collected),
            "total_payouts": float(self.total_payouts),
            "total_open_bets": total_open_bets,
            "total_settled_bets": len([b for b in self.bets.values() if b.status != BetOutcome.PENDING]),
            "contestants": contestants_data,
            "gmv": float(self.total_volume),  # Gross Merchandise Volume
            "rake_percentage": float((self.total_rake_collected / self.total_volume * 100) if self.total_volume > 0 else 0)
        }
    
    def get_user_portfolio(self, user_id: str) -> Optional[UserPortfolio]:
        """Retrieve user's portfolio and performance metrics."""
        return self.user_portfolios.get(user_id)
    
    def get_user_bets(self, user_id: str, status: Optional[BetOutcome] = None) -> List[Bet]:
        """
        Get user's bets, optionally filtered by status.
        
        Args:
            user_id: Target user
            status: Filter by bet status (optional)
            
        Returns:
            List of matching bets
        """
        user_bets = [bet for bet in self.bets.values() if bet.user_id == user_id]
        
        if status:
            user_bets = [bet for bet in user_bets if bet.status == status]
        
        return sorted(user_bets, key=lambda b: b.timestamp, reverse=True)
    
    def close_market(self) -> None:
        """Close the market for new bets."""
        self.is_active = False
        logger.info(f"Market closed: {self.market_name}")
    
    def export_state(self) -> str:
        """Export complete market state as JSON."""
        return json.dumps({
            "competition_id": self.competition_id,
            "market_name": self.market_name,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "total_volume": float(self.total_volume),
            "total_rake_collected": float(self.total_rake_collected),
            "total_payouts": float(self.total_payouts),
            "contestants_count": len(self.contestants),
            "bets_count": len(self.bets),
            "users_count": len(self.user_portfolios)
        }, indent=2)


def create_mock_competition(market_name: str = "Beast Games Championship") -> PredictionMarket:
    """
    Create a mock prediction market with sample data.
    
    Returns:
        PredictionMarket with 5 contestants and sample bets
    """
    market = PredictionMarket("competition_2024_01", market_name)
    
    # Add 5 contestants
    contestants_data = [
        ("Alpha", 0.25),
        ("Beast", 0.20),
        ("Champion", 0.20),
        ("Dynamo", 0.20),
        ("Elite", 0.15)
    ]
    
    for name, prob in contestants_data:
        market.add_contestant(name, prob)
    
    logger.info(f"Mock market created with {len(market.contestants)} contestants")
    
    return market


if __name__ == "__main__":
    # Demo usage
    print("=== BeastBet Live Core Engine Demo ===\n")
    
    market = create_mock_competition()
    
    # Place some bets
    print("Placing sample bets...")
    for user_id in ["user_001", "user_002", "user_003"]:
        contestant_id = list(market.contestants.keys())[0]
        bet = market.place_bet(user_id, contestant_id, Decimal("50"))
        print(f"  {user_id} bet $50 on {market.contestants[contestant_id].name}")
    
    # Show market summary
    print("\n" + market.export_state())
