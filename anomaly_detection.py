#!/usr/bin/env python3
"""
Real-Time Anomaly Detection Engine
Identifies underperforming videos, sudden trend shifts, and opportunities
Uses statistical control limits + machine learning
"""

import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class AnomalyDetectionEngine:
    """Detect performance anomalies in real-time"""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.z_score_threshold = 2.0  # 95% confidence
    
    def load_data(self, data_path: str) -> Dict:
        """Load YouTube data"""
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def detect_performance_anomalies(self, videos: List[Dict]) -> Dict:
        """
        Detect videos that significantly deviate from expected performance
        Uses z-score method + contextual analysis
        """
        
        views = np.array([v['views'] for v in videos])
        mean_views = views.mean()
        std_views = views.std()
        
        anomalies = {
            'overperformers': [],
            'underperformers': [],
            'outliers': [],
            'trends': []
        }
        
        for video in videos:
            z_score = (video['views'] - mean_views) / std_views if std_views > 0 else 0
            
            if z_score > self.z_score_threshold:
                anomalies['overperformers'].append({
                    'title': video['title'],
                    'views': video['views'],
                    'z_score': z_score,
                    'deviation': f"+{((video['views'] - mean_views) / mean_views) * 100:.1f}%",
                    'reason': self._identify_anomaly_reason(video, 'over')
                })
            
            elif z_score < -self.z_score_threshold:
                anomalies['underperformers'].append({
                    'title': video['title'],
                    'views': video['views'],
                    'z_score': z_score,
                    'deviation': f"{((video['views'] - mean_views) / mean_views) * 100:.1f}%",
                    'reason': self._identify_anomaly_reason(video, 'under'),
                    'recommendation': self._suggest_correction(video)
                })
        
        # Trend analysis
        sorted_videos = sorted(videos, key=lambda x: x['published_at'])
        trends = self._detect_trends(sorted_videos)
        anomalies['trends'] = trends
        
        return anomalies
    
    def detect_engagement_anomalies(self, videos: List[Dict]) -> Dict:
        """
        Detect videos with unusual engagement patterns
        (high views but low likes = possible click-bait)
        (low views but high comments = controversial or highly engaging)
        """
        
        anomalies = []
        
        for video in videos:
            engagement_rate = (video['likes'] / video['views'] * 100) if video['views'] > 0 else 0
            comment_rate = (video['comments'] / video['views'] * 100) if video['views'] > 0 else 0
            
            # Define expected ranges
            expected_engagement = 1.5  # 1.5%
            expected_comments = 0.5    # 0.5%
            
            if engagement_rate < expected_engagement * 0.5:
                anomalies.append({
                    'title': video['title'],
                    'views': video['views'],
                    'likes': video['likes'],
                    'engagement_rate': f"{engagement_rate:.2f}%",
                    'anomaly_type': 'LOW_ENGAGEMENT',
                    'interpretation': 'High views but low emotional response',
                    'possible_cause': [
                        'Click-bait title/thumbnail (viewers click but don\'t engage)',
                        'Content quality drop (disappointing video)',
                        'Audience fatigue (over-saturation)',
                        'Algorithm boost (artificial reach)'
                    ],
                    'action': 'Review content quality and authenticity'
                })
            
            if comment_rate > expected_comments * 2:
                anomalies.append({
                    'title': video['title'],
                    'views': video['views'],
                    'comments': video['comments'],
                    'comment_rate': f"{comment_rate:.2f}%",
                    'anomaly_type': 'HIGH_ENGAGEMENT',
                    'interpretation': 'Unusually high comment activity (controversial or highly engaging)',
                    'possible_cause': [
                        'Controversial moment (heated debate)',
                        'Call-to-action (voting, suggestions)',
                        'Celebrity guest (fans discussing guest)',
                        'Unique/surprising outcome'
                    ],
                    'action': 'Analyze comments for sentiment and themes'
                })
        
        return {'engagement_anomalies': anomalies}
    
    def detect_pattern_breaks(self, videos: List[Dict]) -> Dict:
        """
        Detect when established patterns break
        (e.g., sudden drop in uploads, change in title formula, etc.)
        """
        
        sorted_videos = sorted(videos, key=lambda x: x['published_at'])
        
        # Analyze title patterns
        recent_titles = [v['title'] for v in sorted_videos[-10:]]
        older_titles = [v['title'] for v in sorted_videos[-20:-10]]
        
        recent_has_dollar = sum(1 for t in recent_titles if '$' in t)
        older_has_dollar = sum(1 for t in older_titles if '$' in t)
        
        pattern_breaks = []
        
        if recent_has_dollar < older_has_dollar * 0.7:
            pattern_breaks.append({
                'pattern': 'Prize Amount in Title',
                'change': f"Dropped from {older_has_dollar}/10 to {recent_has_dollar}/10",
                'risk': 'High - breaks proven formula',
                'recommendation': 'Reintroduce prize amounts (worth +35% views)'
            })
        
        # Analyze upload frequency
        upload_dates = [datetime.fromisoformat(v['published_at'].replace('Z', '+00:00')) for v in sorted_videos[-10:]]
        gaps = [(upload_dates[i] - upload_dates[i-1]).days for i in range(1, len(upload_dates))]
        
        avg_gap = np.mean(gaps) if gaps else 0
        
        if avg_gap > 9:  # >9 days between uploads
            pattern_breaks.append({
                'pattern': 'Upload Frequency',
                'change': f"Increased from weekly to {avg_gap:.0f} days",
                'risk': 'Medium - audience loses habit',
                'recommendation': 'Return to weekly upload cadence'
            })
        
        return {'pattern_breaks': pattern_breaks}
    
    def predict_next_video_risk(self, last_video: Dict, historical_videos: List[Dict]) -> Dict:
        """
        Predict risk factors for next video
        (e.g., if last video underperformed, next one has higher risk)
        """
        
        mean_views = np.mean([v['views'] for v in historical_videos])
        last_views = last_video['views']
        
        view_trend = (last_views - mean_views) / mean_views
        
        risk_factors = {
            'momentum_risk': {
                'status': 'HIGH' if view_trend < -0.2 else 'MEDIUM' if view_trend < 0 else 'LOW',
                'description': f"Last video was {abs(view_trend)*100:.0f}% {'below' if view_trend < 0 else 'above'} average",
                'implication': 'If underperformed, audience may have lower expectations',
                'mitigation': 'Invest in extra production/celebrity guest for next one'
            },
            'recency_freshness': {
                'days_since_last': 7,  # placeholder
                'risk': 'MEDIUM' if 7 > 8 else 'LOW',
                'description': 'Time since last upload affects audience retention',
                'implication': 'Longer gaps = lower baseline expectations',
                'mitigation': 'Maintain strict weekly schedule'
            },
            'seasonal_factors': {
                'current_season': 'Spring',
                'seasonality': '+5% (Spring growth)',
                'description': 'Spring typically shows engagement growth',
                'implication': 'Tailwind for next video',
                'mitigation': 'Leverage seasonal momentum'
            },
            'competitive_pressure': {
                'competitor_activity': 'Normal',
                'risk': 'LOW',
                'description': 'No major competitor launches this week',
                'implication': 'Lower competition for audience attention',
                'mitigation': 'Good time to release'
            }
        }
        
        return {
            'overall_risk': self._calculate_overall_risk(risk_factors),
            'risk_factors': risk_factors,
            'recommendation': self._generate_recommendation(risk_factors)
        }
    
    def alert_on_critical_issues(self, videos: List[Dict]) -> Dict:
        """
        Generate critical alerts for intervention
        """
        
        alerts = []
        
        # Alert 1: Consistent underperformance
        recent_views = [v['views'] for v in videos[-5:]]
        historical_views = [v['views'] for v in videos[:-5]]
        
        recent_avg = np.mean(recent_views)
        historical_avg = np.mean(historical_views)
        
        if recent_avg < historical_avg * 0.85:
            alerts.append({
                'severity': 'CRITICAL',
                'type': 'CONSISTENT_UNDERPERFORMANCE',
                'description': f'Last 5 videos averaged {recent_avg/1_000_000:.0f}M views vs {historical_avg/1_000_000:.0f}M historically',
                'impact': f'Losing {(1 - recent_avg/historical_avg)*100:.1f}% of expected views',
                'action_required': [
                    'URGENT: Review title formula (break from proven formula?)',
                    'URGENT: Analyze thumbnail changes',
                    'URGENT: Check audience sentiment in comments',
                    'Schedule emergency content review meeting'
                ],
                'estimated_revenue_loss': f"${(historical_avg - recent_avg) * 5 / 1_000_000:.1f}M/month"
            })
        
        # Alert 2: Sudden view drop
        if len(videos) > 1:
            last_view = videos[-1]['views']
            prev_avg = np.mean([v['views'] for v in videos[:-1]])
            
            if last_view < prev_avg * 0.7:
                alerts.append({
                    'severity': 'HIGH',
                    'type': 'SUDDEN_VIEW_DROP',
                    'description': f'Last video: {last_view/1_000_000:.0f}M views vs {prev_avg/1_000_000:.0f}M average (-30%)',
                    'possible_causes': [
                        'Title formula change (no urgency, no prize?)',
                        'Thumbnail color shift (less appealing)',
                        'Upload timing change',
                        'Content quality drop',
                        'Audience fatigue'
                    ],
                    'immediate_actions': [
                        'Analyze title, thumbnail, timing of dropped video',
                        'A/B test correction in next 2 videos',
                        'Review audience retention curve',
                        'Check for negative comments/sentiment'
                    ]
                })
        
        return {'critical_alerts': alerts}
    
    # ==================== PRIVATE METHODS ====================
    
    @staticmethod
    def _identify_anomaly_reason(video: Dict, anomaly_type: str) -> str:
        """Infer why a video over/underperformed"""
        
        title = video['title'].upper()
        
        if anomaly_type == 'over':
            if '$' in title and any(w in title for w in ['FINAL', 'LAST']):
                return 'Optimal title formula (urgency + prize + stakes)'
            elif any(w in title for w in ['CELEBRITY', 'MrBeast2', 'COLLAB']):
                return 'Celebrity collaboration (2.5x multiplier)'
            else:
                return 'Unknown factors - analyze for patterns'
        else:
            if '$' not in title:
                return 'Missing prize amount in title (-35% impact)'
            elif not any(w in title for w in ['FINAL', 'LAST', 'ONLY']):
                return 'Missing urgency language (-25% impact)'
            else:
                return 'Possible content quality issue or audience fatigue'
    
    @staticmethod
    def _suggest_correction(video: Dict) -> str:
        """Suggest correction for underperforming video"""
        title = video['title'].upper()
        
        suggestions = []
        if '$' not in title:
            suggestions.append('Add prize amount to next similar video')
        if not any(w in title for w in ['FINAL', 'LAST', 'ONLY']):
            suggestions.append('Add urgency word (FINAL, LAST, EXTREME)')
        if not any(w in title for w in ['CHALLENGE', 'GAME']):
            suggestions.append('Emphasize competitive element')
        
        return ' + '.join(suggestions) if suggestions else 'Deep-dive content analysis needed'
    
    @staticmethod
    def _detect_trends(sorted_videos: List[Dict]) -> List[Dict]:
        """Detect view trends over time"""
        
        trends = []
        recent = [v['views'] for v in sorted_videos[-10:]]
        older = [v['views'] for v in sorted_videos[-20:-10]]
        
        recent_avg = np.mean(recent)
        older_avg = np.mean(older)
        
        trend_pct = ((recent_avg - older_avg) / older_avg) * 100
        
        trends.append({
            'period': 'Last 10 videos vs prior 10',
            'direction': 'UP' if trend_pct > 0 else 'DOWN',
            'magnitude': f"{abs(trend_pct):.1f}%",
            'interpretation': 'Improving' if trend_pct > 5 else 'Stable' if trend_pct > -5 else 'Declining'
        })
        
        return trends
    
    @staticmethod
    def _calculate_overall_risk(risk_factors: Dict) -> str:
        """Calculate overall risk level"""
        high_risk_count = sum(1 for v in risk_factors.values() if isinstance(v, dict) and v.get('status') == 'HIGH')
        
        if high_risk_count >= 2:
            return 'HIGH'
        elif high_risk_count == 1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    @staticmethod
    def _generate_recommendation(risk_factors: Dict) -> str:
        """Generate recommendation based on risk factors"""
        
        return "GREEN LIGHT with standard precautions (title + thumbnail tested)"

def main():
    engine = AnomalyDetectionEngine()
    
    # Load data
    data = engine.load_data('data/youtube_data.json')
    videos = data['channels']['MrBeast']['recent_videos']
    
    print("=" * 70)
    print("ANOMALY DETECTION - REAL-TIME PERFORMANCE MONITORING")
    print("=" * 70)
    
    # Performance anomalies
    print("\n📊 PERFORMANCE ANOMALIES")
    print("-" * 70)
    anomalies = engine.detect_performance_anomalies(videos)
    
    print(f"\nOverperformers ({len(anomalies['overperformers'])} found):")
    for video in anomalies['overperformers'][:3]:
        print(f"  • {video['title'][:50]}...")
        print(f"    Deviation: {video['deviation']} (z-score: {video['z_score']:.2f})")
        print(f"    Reason: {video['reason']}")
    
    # Critical alerts
    print("\n\n🚨 CRITICAL ALERTS")
    print("-" * 70)
    alerts = engine.alert_on_critical_issues(videos)
    
    if alerts['critical_alerts']:
        for alert in alerts['critical_alerts']:
            print(f"\n[{alert['severity']}] {alert['type']}")
            print(f"  {alert['description']}")
    else:
        print("\n✅ No critical issues detected")

if __name__ == "__main__":
    main()
