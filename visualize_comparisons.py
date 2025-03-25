import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
from datetime import datetime
import os

def create_comparison_visualization(data_list, labels=None, output_file=None):
    """
    Create a visualization comparing multiple sets of match rate measurements.
    
    Parameters:
    data_list (list): List of dictionaries, each containing match rate measurements
    labels (list): Labels for each measurement set (optional)
    output_file (str): Path to save the visualization (optional)
    """
    # Validate input
    if not data_list:
        print("Error: No data provided for visualization")
        return
    
    # Create DataFrame from the data
    df_data = []
    
    for i, data in enumerate(data_list):
        # Use provided label or default
        label = labels[i] if labels and i < len(labels) else f"Measurement {i+1}"
        
        # Extract match rates
        severity = data.get('Severity Match Rate (%)', data.get('severity_match_rate', 0))
        occurrence = data.get('Occurrence Match Rate (%)', data.get('occurrence_match_rate', 0))
        priority = data.get('Priority Match Rate (%)', data.get('priority_match_rate', 0))
        
        # Convert to numeric values
        try:
            severity = float(severity)
            occurrence = float(occurrence)
            priority = float(priority)
        except (ValueError, TypeError):
            print(f"Warning: Could not convert values to float for {label}")
            continue
            
        # Add to data list
        df_data.append({
            'Measurement': label,
            'Metric': 'Severity',
            'Match Rate (%)': severity
        })
        df_data.append({
            'Measurement': label,
            'Metric': 'Occurrence',
            'Match Rate (%)': occurrence
        })
        df_data.append({
            'Measurement': label,
            'Metric': 'Priority',
            'Match Rate (%)': priority
        })
    
    # Create DataFrame
    df = pd.DataFrame(df_data)
    
    # Set up the visualization style
    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 8))
    
    # Create the grouped bar chart
    chart = sns.barplot(
        x='Metric', 
        y='Match Rate (%)', 
        hue='Measurement', 
        data=df,
        palette='viridis'
    )
    
    # Add average lines for each metric
    for metric in ['Severity', 'Occurrence', 'Priority']:
        # Get the average for this metric
        metric_avg = df[df['Metric'] == metric]['Match Rate (%)'].mean()
        
        # Calculate the x position for this metric
        metric_positions = [p.get_x() + p.get_width() / 2 for p in chart.patches 
                          if p.get_x() == chart.patches[df[df['Metric'] == metric].index[0]].get_x()]
        x_min = min(metric_positions) - 0.2
        x_max = max(metric_positions) + 0.2
        
        # Draw the average line
        plt.plot([x_min, x_max], [metric_avg, metric_avg], 'r--', linewidth=1.5)
        
        # Add average text
        plt.text(x_max + 0.05, metric_avg, f'Avg: {metric_avg:.1f}%', 
                va='center', ha='left', color='red', fontsize=10)
    
    # Customize the chart
    plt.title('Comparison of Match Rates Across Measurements', fontsize=16)
    plt.xlabel('Assessment Metric', fontsize=14)
    plt.ylabel('Match Rate (%)', fontsize=14)
    plt.ylim(0, 100)  # Set y-axis from 0 to 100%
    
    # Add value labels on top of bars
    for p in chart.patches:
        chart.annotate(
            f'{p.get_height():.1f}%', 
            (p.get_x() + p.get_width() / 2., p.get_height()), 
            ha='center', va='bottom', fontsize=9
        )
    
    # Adjust legend and layout
    plt.legend(title='Measurement', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Save or display the chart
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {output_file}")
    else:
        plt.show()
    
    # Create a detailed comparison table
    print("\n=== DETAILED COMPARISON ===\n")
    
    # Pivot the data for a cleaner display
    pivot_df = df.pivot(index='Measurement', columns='Metric', values='Match Rate (%)')
    
    # Calculate metric averages across all measurements
    metric_averages = pivot_df.mean(axis=0)
    
    # Add the averages as a new row
    pivot_df.loc['AVERAGE'] = metric_averages
    
    # Print the table
    print(pivot_df.round(2))
    print("\nKey Insights:")
    print(f"- Average Severity Match Rate: {metric_averages['Severity']:.2f}%")
    print(f"- Average Occurrence Match Rate: {metric_averages['Occurrence']:.2f}%")
    print(f"- Average Priority Match Rate: {metric_averages['Priority']:.2f}%")
    print(f"- Overall Average Match Rate: {metric_averages.mean():.2f}%")
    
    # Save the comparison table if requested
    if output_file:
        csv_output = output_file.replace('.png', '.csv').replace('.jpg', '.csv')
        pivot_df.round(2).to_csv(csv_output)
        print(f"Comparison table saved to {csv_output}")
        
        # Save as Excel if pandas has Excel support
        try:
            excel_output = output_file.replace('.png', '.xlsx').replace('.jpg', '.xlsx')
            pivot_df.round(2).to_excel(excel_output)
            print(f"Comparison table also saved to {excel_output}")
        except:
            pass

def parse_txt_file(file_path):
    """
    Parse a match rates .txt file to extract the match rates.
    Returns a dictionary with the match rates.
    """
    match_rates = {}
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Extract match rates using string parsing
            for line in content.split('\n'):
                if 'Severity Match Rate' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        match_rates['Severity Match Rate (%)'] = float(parts[1].strip())
                elif 'Occurrence Match Rate' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        match_rates['Occurrence Match Rate (%)'] = float(parts[1].strip())
                elif 'Priority Match Rate' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        match_rates['Priority Match Rate (%)'] = float(parts[1].strip())
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
    
    return match_rates

def parse_csv_file(file_path):
    """
    Parse a match rates .csv file to extract the match rates.
    Returns a dictionary with the match rates.
    """
    try:
        df = pd.read_csv(file_path)
        
        match_rates = {}
        
        # Look for column names that might contain match rate data
        for col in df.columns:
            if 'severity' in col.lower() and 'match' in col.lower() and 'rate' in col.lower():
                match_rates['Severity Match Rate (%)'] = df[col].iloc[0]
            elif 'occurrence' in col.lower() and 'match' in col.lower() and 'rate' in col.lower():
                match_rates['Occurrence Match Rate (%)'] = df[col].iloc[0]
            elif 'priority' in col.lower() and 'match' in col.lower() and 'rate' in col.lower():
                match_rates['Priority Match Rate (%)'] = df[col].iloc[0]
        
        return match_rates
    except Exception as e:
        print(f"Error parsing CSV file {file_path}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Create a visual comparison of match rate measurements.')
    parser.add_argument('--files', nargs='+', help='List of match rate files (txt or csv)')
    parser.add_argument('--labels', nargs='+', help='Labels for each measurement set')
    parser.add_argument('--manual', action='store_true', help='Enter measurements manually')
    parser.add_argument('--output', help='Output file path for the visualization')
    
    args = parser.parse_args()
    
    data_list = []
    labels = args.labels or []
    
    # Process files if provided
    if args.files:
        for i, file_path in enumerate(args.files):
            if file_path.endswith('.txt'):
                data = parse_txt_file(file_path)
            elif file_path.endswith('.csv'):
                data = parse_csv_file(file_path)
            else:
                print(f"Unsupported file format: {file_path}")
                continue
                
            if data:
                data_list.append(data)
                
                # If label not provided, use filename
                if i >= len(labels):
                    file_name = os.path.basename(file_path)
                    labels.append(file_name)
    
    # Manual entry if requested or if no files provided
    if args.manual or not data_list:
        print("\nManual Entry Mode")
        print("=================")
        
        num_measurements = int(input("Enter number of measurements: "))
        
        for i in range(num_measurements):
            print(f"\nMeasurement {i+1}:")
            
            if i >= len(labels):
                label = input(f"Label for Measurement {i+1}: ")
                labels.append(label)
            
            severity = float(input("Severity Match Rate (%): "))
            occurrence = float(input("Occurrence Match Rate (%): "))
            priority = float(input("Priority Match Rate (%): "))
            
            data_list.append({
                'Severity Match Rate (%)': severity,
                'Occurrence Match Rate (%)': occurrence,
                'Priority Match Rate (%)': priority
            })
    
    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"match_rates_comparison_{timestamp}.png"
    
    # Create the visualization
    create_comparison_visualization(data_list, labels, args.output)

if __name__ == "__main__":
    main()