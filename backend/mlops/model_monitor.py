"""
Model Monitoring: Track model performance and detect drift
"""
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelMonitor:
    """Monitor model performance and detect potential issues"""
    
    def __init__(self, log_file: str = "logs/predictions.jsonl"):
        self.log_file = Path(log_file)
    
    def load_predictions_by_timeframe(self, days: int = 7) -> list:
        """Load predictions from the last N days"""
        if not self.log_file.exists():
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        predictions = []
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    
                    if timestamp >= cutoff_date:
                        predictions.append(entry)
                except Exception as e:
                    logger.error(f"Error parsing line: {e}")
        
        return predictions
    
    def detect_confidence_drift(self, window_size: int = 100) -> dict:
        """Detect if model confidence is drifting over time"""
        predictions = self.load_predictions_by_timeframe(days=30)
        
        if len(predictions) < window_size * 2:
            return {'status': 'insufficient_data', 'message': 'Need more predictions for drift detection'}
        
        # Split into windows
        confidences = [p['prediction']['confidence'] for p in predictions]
        
        # Compare first and last windows
        first_window = confidences[:window_size]
        last_window = confidences[-window_size:]
        
        first_avg = np.mean(first_window)
        last_avg = np.mean(last_window)
        
        drift = abs(first_avg - last_avg)
        drift_percentage = (drift / first_avg) * 100
        
        status = 'stable'
        if drift_percentage > 10:
            status = 'significant_drift'
        elif drift_percentage > 5:
            status = 'minor_drift'
        
        return {
            'status': status,
            'first_window_avg_confidence': first_avg,
            'last_window_avg_confidence': last_avg,
            'drift': drift,
            'drift_percentage': drift_percentage,
            'recommendation': self._get_drift_recommendation(status)
        }
    
    def _get_drift_recommendation(self, status: str) -> str:
        """Get recommendation based on drift status"""
        if status == 'significant_drift':
            return "Consider retraining the model with recent data"
        elif status == 'minor_drift':
            return "Monitor closely, retraining may be needed soon"
        return "Model performance is stable"
    
    def analyze_prediction_distribution(self) -> dict:
        """Analyze the distribution of predictions over time"""
        predictions = self.load_predictions_by_timeframe(days=7)
        
        if not predictions:
            return {'status': 'no_data'}
        
        daily_stats = defaultdict(lambda: {'sarcastic': 0, 'total': 0})
        
        for pred in predictions:
            date = pred['timestamp'][:10]  # Get date part
            daily_stats[date]['total'] += 1
            if pred['prediction']['is_sarcastic']:
                daily_stats[date]['sarcastic'] += 1
        
        # Calculate daily sarcasm rates
        daily_rates = {}
        for date, stats in daily_stats.items():
            daily_rates[date] = stats['sarcastic'] / stats['total'] if stats['total'] > 0 else 0
        
        overall_rate = sum(s['sarcastic'] for s in daily_stats.values()) / \
                      sum(s['total'] for s in daily_stats.values())
        
        # Detect anomalies (days with unusually high/low sarcasm rates)
        rates = list(daily_rates.values())
        if len(rates) > 1:
            std_dev = np.std(rates)
            mean_rate = np.mean(rates)
            
            anomalies = []
            for date, rate in daily_rates.items():
                if abs(rate - mean_rate) > 2 * std_dev:
                    anomalies.append({
                        'date': date,
                        'rate': rate,
                        'deviation': abs(rate - mean_rate) / std_dev
                    })
        else:
            anomalies = []
        
        return {
            'overall_sarcasm_rate': overall_rate,
            'daily_rates': daily_rates,
            'daily_counts': {k: v['total'] for k, v in daily_stats.items()},
            'anomalies': anomalies,
            'status': 'anomalies_detected' if anomalies else 'normal'
        }
    
    def check_model_health(self) -> dict:
        """Comprehensive model health check"""
        predictions = self.load_predictions_by_timeframe(days=7)
        
        if not predictions:
            return {
                'status': 'unhealthy',
                'reason': 'no_recent_predictions',
                'message': 'No predictions in the last 7 days'
            }
        
        # Check average confidence
        confidences = [p['prediction']['confidence'] for p in predictions]
        avg_confidence = np.mean(confidences)
        
        # Check prediction rate consistency
        sarcasm_rate = sum(1 for p in predictions if p['prediction']['is_sarcastic']) / len(predictions)
        
        # Health criteria
        health_issues = []
        
        if avg_confidence < 0.6:
            health_issues.append("Low average confidence")
        
        if sarcasm_rate > 0.8 or sarcasm_rate < 0.05:
            health_issues.append("Extreme sarcasm detection rate")
        
        if len(predictions) < 10:
            health_issues.append("Low prediction volume")
        
        # Drift check
        drift = self.detect_confidence_drift()
        if drift.get('status') == 'significant_drift':
            health_issues.append("Significant confidence drift detected")
        
        status = 'healthy' if not health_issues else 'needs_attention'
        
        return {
            'status': status,
            'prediction_count': len(predictions),
            'avg_confidence': avg_confidence,
            'sarcasm_rate': sarcasm_rate,
            'issues': health_issues,
            'drift_analysis': drift,
            'recommendation': self._get_health_recommendation(health_issues)
        }
    
    def _get_health_recommendation(self, issues: list) -> str:
        """Get recommendation based on health issues"""
        if not issues:
            return "Model is performing well"
        
        recommendations = []
        if "Low average confidence" in issues:
            recommendations.append("Review model architecture or retrain with more data")
        if "Extreme sarcasm detection rate" in issues:
            recommendations.append("Check for data imbalance or model bias")
        if "Low prediction volume" in issues:
            recommendations.append("Ensure the extension is properly deployed")
        if "Significant confidence drift detected" in issues:
            recommendations.append("Retrain model with recent data")
        
        return "; ".join(recommendations)
    
    def generate_monitoring_report(self, output_file: str = "reports/monitoring_report.json"):
        """Generate comprehensive monitoring report"""
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'health_check': self.check_model_health(),
            'distribution_analysis': self.analyze_prediction_distribution(),
            'drift_detection': self.detect_confidence_drift()
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Monitoring report saved to {output_path}")
        return report


def main():
    """Run model monitoring"""
    monitor = ModelMonitor()
    
    print("\n" + "="*60)
    print("MODEL MONITORING REPORT")
    print("="*60 + "\n")
    
    # Health check
    health = monitor.check_model_health()
    print("HEALTH STATUS:", health['status'].upper())
    print(f"Predictions (7 days): {health.get('prediction_count', 0)}")
    print(f"Average Confidence: {health.get('avg_confidence', 0):.4f}")
    print(f"Sarcasm Rate: {health.get('sarcasm_rate', 0):.2%}")
    
    if health.get('issues'):
        print("\nISSUES DETECTED:")
        for issue in health['issues']:
            print(f"  - {issue}")
    
    print(f"\nRECOMMENDATION: {health.get('recommendation')}")
    
    # Distribution analysis
    dist = monitor.analyze_prediction_distribution()
    if dist.get('anomalies'):
        print(f"\nANOMALIES: {len(dist['anomalies'])} days with unusual activity")
    
    # Generate full report
    monitor.generate_monitoring_report()
    print("\nFull report saved to reports/monitoring_report.json")


if __name__ == "__main__":
    main()
