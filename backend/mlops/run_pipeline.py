"""
Run complete MLOps pipeline: analysis, monitoring, and reporting
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from prediction_analyzer import PredictionAnalyzer
from model_monitor import ModelMonitor
import json
from datetime import datetime


def main():
    print("=" * 70)
    print("SARCASM DETECTION SYSTEM - MLOPS PIPELINE")
    print("=" * 70)
    print(f"\nRun started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Initialize components
    analyzer = PredictionAnalyzer()
    monitor = ModelMonitor()
    
    # 1. Run Prediction Analysis
    print("\n" + "-" * 70)
    print("1. PREDICTION ANALYSIS")
    print("-" * 70)
    
    stats = analyzer.get_statistics()
    if stats:
        print(f"Total Predictions: {stats['total_predictions']}")
        print(f"Sarcastic: {stats['sarcastic_count']} ({stats['sarcasm_rate']*100:.2f}%)")
        print(f"Non-Sarcastic: {stats['non_sarcastic_count']}")
        print(f"Average Confidence: {stats['avg_confidence']:.4f}")
        
        print("\nPlatform Distribution:")
        for platform, count in stats['platform_distribution'].items():
            print(f"  {platform.capitalize()}: {count}")
        
        # Export for retraining
        export_path = analyzer.export_for_retraining()
        print(f"\nRetraining data exported to: {export_path}")
        
        # Check low confidence samples
        low_conf = analyzer.get_low_confidence_samples(threshold=0.7)
        if not low_conf.empty:
            print(f"\nFound {len(low_conf)} low confidence predictions for review")
        
        # Generate report
        analyzer.generate_report()
        print("Detailed report saved to: reports/prediction_report.txt")
    else:
        print("No predictions found. Start using the system to collect data.")
    
    # 2. Run Model Monitoring
    print("\n" + "-" * 70)
    print("2. MODEL HEALTH MONITORING")
    print("-" * 70)
    
    health = monitor.check_model_health()
    print(f"Health Status: {health['status'].upper()}")
    
    if health.get('prediction_count'):
        print(f"Recent Predictions (7 days): {health['prediction_count']}")
        print(f"Average Confidence: {health.get('avg_confidence', 0):.4f}")
        print(f"Sarcasm Rate: {health.get('sarcasm_rate', 0):.2%}")
        
        if health.get('issues'):
            print("\n??  Issues Detected:")
            for issue in health['issues']:
                print(f"  - {issue}")
        else:
            print("\n? No issues detected")
        
        print(f"\nRecommendation: {health.get('recommendation')}")
    
    # 3. Drift Detection
    print("\n" + "-" * 70)
    print("3. DRIFT DETECTION")
    print("-" * 70)
    
    drift = monitor.detect_confidence_drift()
    print(f"Status: {drift.get('status', 'unknown').upper()}")
    
    if drift.get('status') != 'insufficient_data':
        print(f"First Window Avg: {drift.get('first_window_avg_confidence', 0):.4f}")
        print(f"Last Window Avg: {drift.get('last_window_avg_confidence', 0):.4f}")
        print(f"Drift: {drift.get('drift_percentage', 0):.2f}%")
        print(f"Recommendation: {drift.get('recommendation')}")
    else:
        print(drift.get('message', 'Insufficient data'))
    
    # 4. Distribution Analysis
    print("\n" + "-" * 70)
    print("4. PREDICTION DISTRIBUTION")
    print("-" * 70)
    
    dist = monitor.analyze_prediction_distribution()
    if dist.get('status') != 'no_data':
        print(f"Overall Sarcasm Rate: {dist.get('overall_sarcasm_rate', 0):.2%}")
        
        if dist.get('daily_counts'):
            print("\nDaily Prediction Counts:")
            for date, count in sorted(dist['daily_counts'].items())[-7:]:
                rate = dist['daily_rates'].get(date, 0)
                print(f"  {date}: {count} predictions ({rate:.2%} sarcastic)")
        
        if dist.get('anomalies'):
            print(f"\n??  Anomalies detected: {len(dist['anomalies'])} days")
            for anomaly in dist['anomalies'][:3]:
                print(f"  {anomaly['date']}: {anomaly['rate']:.2%} sarcasm rate")
    
    # 5. Generate Comprehensive Report
    print("\n" + "-" * 70)
    print("5. GENERATING COMPREHENSIVE REPORT")
    print("-" * 70)
    
    report = monitor.generate_monitoring_report()
    print("Monitoring report saved to: reports/monitoring_report.json")
    
    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    
    summary = {
        'predictions_analyzed': stats.get('total_predictions', 0) if stats else 0,
        'health_status': health.get('status', 'unknown'),
        'drift_status': drift.get('status', 'unknown'),
        'anomalies_detected': len(dist.get('anomalies', [])),
        'reports_generated': 2
    }
    
    print(json.dumps(summary, indent=2))
    
    print(f"\nPipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Return status code
    if health.get('status') == 'healthy' and drift.get('status') in ['stable', 'insufficient_data']:
        return 0  # Success
    else:
        return 1  # Issues detected


if __name__ == "__main__":
    sys.exit(main())
