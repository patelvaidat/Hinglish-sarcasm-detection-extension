"""
MLOps: Prediction Logger and Model Retraining Pipeline
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionAnalyzer:
    """Analyze logged predictions for model improvement"""
    
    def __init__(self, log_file: str = "logs/predictions.jsonl"):
        self.log_file = Path(log_file)
    
    def load_predictions(self) -> pd.DataFrame:
        """Load all predictions from JSONL file"""
        if not self.log_file.exists():
            logger.warning(f"Log file {self.log_file} does not exist")
            return pd.DataFrame()
        
        predictions = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    predictions.append({
                        'timestamp': entry['timestamp'],
                        'text': entry['text'],
                        'is_sarcastic': entry['prediction']['is_sarcastic'],
                        'confidence': entry['prediction']['confidence'],
                        'sarcasm_score': entry['prediction']['sarcasm_score'],
                        'platform': entry['metadata'].get('platform', 'unknown'),
                        'post_id': entry['metadata'].get('post_id', '')
                    })
                except Exception as e:
                    logger.error(f"Error parsing line: {e}")
        
        return pd.DataFrame(predictions)
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics from predictions"""
        df = self.load_predictions()
        
        if df.empty:
            return {}
        
        stats = {
            'total_predictions': len(df),
            'sarcastic_count': df['is_sarcastic'].sum(),
            'non_sarcastic_count': (~df['is_sarcastic']).sum(),
            'sarcasm_rate': df['is_sarcastic'].mean(),
            'avg_confidence': df['confidence'].mean(),
            'avg_sarcasm_score': df['sarcasm_score'].mean(),
            'platform_distribution': df['platform'].value_counts().to_dict(),
            'confidence_distribution': {
                'high (>0.8)': (df['confidence'] > 0.8).sum(),
                'medium (0.5-0.8)': ((df['confidence'] >= 0.5) & (df['confidence'] <= 0.8)).sum(),
                'low (<0.5)': (df['confidence'] < 0.5).sum()
            }
        }
        
        return stats
    
    def export_for_retraining(self, output_file: str = "data/retraining_data.csv"):
        """Export predictions in format suitable for retraining"""
        df = self.load_predictions()
        
        if df.empty:
            logger.warning("No predictions to export")
            return
        
        # Prepare data for retraining
        retraining_df = df[['text', 'is_sarcastic', 'confidence', 'sarcasm_score']]
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        retraining_df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(retraining_df)} predictions to {output_path}")
        
        return output_path
    
    def get_low_confidence_samples(self, threshold: float = 0.6) -> pd.DataFrame:
        """Get samples with low confidence for manual review"""
        df = self.load_predictions()
        
        if df.empty:
            return df
        
        low_conf = df[df['confidence'] < threshold]
        return low_conf.sort_values('confidence')
    
    def generate_report(self, output_file: str = "reports/prediction_report.txt"):
        """Generate a comprehensive analysis report"""
        stats = self.get_statistics()
        
        if not stats:
            logger.warning("No statistics to report")
            return
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SARCASM DETECTION MODEL - PREDICTION ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("OVERALL STATISTICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Predictions: {stats['total_predictions']}\n")
            f.write(f"Sarcastic: {stats['sarcastic_count']} ({stats['sarcasm_rate']*100:.2f}%)\n")
            f.write(f"Non-Sarcastic: {stats['non_sarcastic_count']} "
                   f"({(1-stats['sarcasm_rate'])*100:.2f}%)\n\n")
            
            f.write(f"Average Confidence: {stats['avg_confidence']:.4f}\n")
            f.write(f"Average Sarcasm Score: {stats['avg_sarcasm_score']:.4f}\n\n")
            
            f.write("PLATFORM DISTRIBUTION\n")
            f.write("-" * 60 + "\n")
            for platform, count in stats['platform_distribution'].items():
                f.write(f"{platform.capitalize()}: {count}\n")
            f.write("\n")
            
            f.write("CONFIDENCE DISTRIBUTION\n")
            f.write("-" * 60 + "\n")
            for level, count in stats['confidence_distribution'].items():
                f.write(f"{level}: {count}\n")
            
        logger.info(f"Report generated at {output_path}")


def main():
    """Main function to run analysis"""
    analyzer = PredictionAnalyzer()
    
    # Get statistics
    stats = analyzer.get_statistics()
    print("\nPrediction Statistics:")
    print(json.dumps(stats, indent=2, default=str))
    
    # Export for retraining
    analyzer.export_for_retraining()
    
    # Get low confidence samples
    low_conf = analyzer.get_low_confidence_samples(threshold=0.7)
    if not low_conf.empty:
        print(f"\nFound {len(low_conf)} low confidence predictions")
        print("\nSample low confidence predictions:")
        print(low_conf[['text', 'is_sarcastic', 'confidence']].head(10))
    
    # Generate report
    analyzer.generate_report()
    print("\nAnalysis complete! Check reports/prediction_report.txt")


if __name__ == "__main__":
    main()
