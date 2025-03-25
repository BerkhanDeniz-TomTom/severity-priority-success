import pandas as pd
import argparse

def standardize_severity(severity):
    """Map severity values using the provided exact mappings."""
    if severity is None:
        return None
        
    # AI severity mapping
    ai_severity_map = {
        'CRITICAL (A)': 'A - SHOWSTOPPER',
        'MAJOR (B)': 'B - MAJOR',
        'MINOR (C)': 'C - MINOR',
        'SAFETY': 'S - SAFETY ONLY'
    }
    
    # User severity mapping
    user_severity_map = {
        'A - SHOWSTOPPER': 'A - SHOWSTOPPER',
        'B - MAJOR': 'B - MAJOR',
        'C - MINOR': 'C - MINOR',
        'S - SAFETY ONLY': 'S - SAFETY ONLY'
    }
    
    severity = str(severity).upper()
    
    # Check if it's an AI severity value
    for ai_val, mapped_val in ai_severity_map.items():
        if ai_val in severity:
            return mapped_val
            
    # Check if it's a user severity value
    for user_val, mapped_val in user_severity_map.items():
        if user_val in severity:
            return mapped_val
            
    return severity

def standardize_occurrence(occurrence):
    """Map occurrence values using the provided exact mappings."""
    if occurrence is None:
        return None
        
    # AI occurrence mapping
    ai_occurrence_map = {
        'CERTAIN': 'CERTAIN',
        'VERY FREQUENT': 'VERY FREQUENT',
        'FREQUENT': 'FREQUENT',
        'RARE': 'RARE'
    }
    
    # User occurrence to AI occurrence mapping
    user_to_ai_map = {
        'ONCE': 'RARE',
        'RARELY': 'RARE',
        'UNDETERMINED': 'RARE',
        'INTERMITTENT': 'RARE',
        'LOW OCCURRENCE': 'RARE',
        'SOMETIMES': 'RARE',
        '25%': 'FREQUENT',
        '50%': 'FREQUENT',
        '75%': 'FREQUENT',
        'ALWAYS': 'CERTAIN',
        'FREQUENTLY': 'FREQUENT'
    }
    
    occurrence = str(occurrence).upper()
    
    # Check if it's an AI occurrence value
    for ai_val, mapped_val in ai_occurrence_map.items():
        if occurrence == ai_val:
            return mapped_val
            
    # Check if it's a user occurrence value
    for user_val, mapped_val in user_to_ai_map.items():
        if occurrence == user_val:
            return mapped_val
            
    # Handle percentage values that might not be exact matches
    if '%' in occurrence:
        try:
            percentage = float(occurrence.replace('%', '').strip())
            if percentage <= 25:
                return 'FREQUENT'
            elif percentage <= 75:
                return 'VERY FREQUENT'
            else:
                return 'CERTAIN'
        except ValueError:
            pass
            
    return occurrence

def standardize_priority(priority):
    """Map priority values using the provided exact mappings."""
    if priority is None:
        return None
        
    # AI priority mapping
    ai_priority_map = {
        'BLOCKER': 'BLOCKER',
        'URGENT': 'CRITICAL',
        'HIGH': 'MAJOR',
        'MEDIUM': 'MAJOR',
        'LOW': 'MINOR'
    }
    
    # User priority mapping
    user_priority_map = {
        'BLOCKER': 'BLOCKER',
        'CRITICAL': 'CRITICAL',
        'MAJOR': 'MAJOR',
        'MINOR': 'MINOR'
    }
    
    priority = str(priority).upper()
    
    # Check if it's an AI priority value
    for ai_val, mapped_val in ai_priority_map.items():
        if ai_val == priority:
            return mapped_val
            
    # Check if it's a user priority value
    for user_val, mapped_val in user_priority_map.items():
        if user_val == priority:
            return mapped_val
            
    return priority

def calculate_match_rates(df):
    """Calculate match rates between user and AI assessments."""
    # Check for required columns
    required_columns = [
        'user_severity', 'ai_severity',
        'user_occurrence', 'ai_occurrence',
        'user_priority', 'ai_priority'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Warning: Missing columns in CSV: {', '.join(missing_columns)}")
        return None
    
    # Handle potential missing values
    metrics_df = df[required_columns].copy()
    
    # Apply standardization to all columns for fair comparison
    metrics_df['user_severity_std'] = metrics_df['user_severity'].apply(standardize_severity)
    metrics_df['ai_severity_std'] = metrics_df['ai_severity'].apply(standardize_severity)
    metrics_df['user_occurrence_std'] = metrics_df['user_occurrence'].apply(standardize_occurrence)
    metrics_df['ai_occurrence_std'] = metrics_df['ai_occurrence'].apply(standardize_occurrence)
    metrics_df['user_priority_std'] = metrics_df['user_priority'].apply(standardize_priority)
    metrics_df['ai_priority_std'] = metrics_df['ai_priority'].apply(standardize_priority)
    
    # Calculate match flags
    metrics_df['severity_match'] = metrics_df['user_severity_std'] == metrics_df['ai_severity_std']
    metrics_df['occurrence_match'] = metrics_df['user_occurrence_std'] == metrics_df['ai_occurrence_std']
    metrics_df['priority_match'] = metrics_df['user_priority_std'] == metrics_df['ai_priority_std']
    
    # Count total valid comparisons (excluding rows with None in either column)
    valid_severity = metrics_df[['user_severity_std', 'ai_severity_std']].notna().all(axis=1).sum()
    valid_occurrence = metrics_df[['user_occurrence_std', 'ai_occurrence_std']].notna().all(axis=1).sum()
    valid_priority = metrics_df[['user_priority_std', 'ai_priority_std']].notna().all(axis=1).sum()
    
    # Calculate match rates
    severity_match_rate = (metrics_df['severity_match'].sum() / valid_severity * 100) if valid_severity > 0 else 0
    occurrence_match_rate = (metrics_df['occurrence_match'].sum() / valid_occurrence * 100) if valid_occurrence > 0 else 0
    priority_match_rate = (metrics_df['priority_match'].sum() / valid_priority * 100) if valid_priority > 0 else 0
    
    # Calculate overall match (all three dimensions match)
    metrics_df['all_match'] = metrics_df['severity_match'] & metrics_df['occurrence_match'] & metrics_df['priority_match']
    valid_all = (metrics_df[['user_severity_std', 'ai_severity_std',
                            'user_occurrence_std', 'ai_occurrence_std',
                            'user_priority_std', 'ai_priority_std']].notna().all(axis=1)).sum()
    overall_match_rate = (metrics_df['all_match'].sum() / valid_all * 100) if valid_all > 0 else 0
    
    # Create results dictionary
    results = {
        'Severity Match Rate (%)': round(severity_match_rate, 2),
        'Occurrence Match Rate (%)': round(occurrence_match_rate, 2),
        'Priority Match Rate (%)': round(priority_match_rate, 2),
        'Overall Match Rate (%)': round(overall_match_rate, 2),
        'Total Issues Analyzed': len(df),
        'Valid Severity Comparisons': valid_severity,
        'Valid Occurrence Comparisons': valid_occurrence,
        'Valid Priority Comparisons': valid_priority
    }
    
    return results, metrics_df

def print_detailed_breakdown(metrics_df):
    """Print detailed breakdown of mismatches."""
    print("\n=== DETAILED BREAKDOWN ===\n")
    
    # Severity breakdown
    print("SEVERITY MISMATCHES:")
    severity_cross = pd.crosstab(
        metrics_df['user_severity_std'], 
        metrics_df['ai_severity_std'],
        margins=True, 
        normalize=False
    )
    print(severity_cross)
    print()
    
    # Occurrence breakdown
    print("OCCURRENCE MISMATCHES:")
    occurrence_cross = pd.crosstab(
        metrics_df['user_occurrence_std'], 
        metrics_df['ai_occurrence_std'],
        margins=True, 
        normalize=False
    )
    print(occurrence_cross)
    print()
    
    # Priority breakdown
    print("PRIORITY MISMATCHES:")
    priority_cross = pd.crosstab(
        metrics_df['user_priority_std'], 
        metrics_df['ai_priority_std'],
        margins=True, 
        normalize=False
    )
    print(priority_cross)

def main():
    parser = argparse.ArgumentParser(description='Calculate AI vs User assessment match rates from CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file containing issue data')
    parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown of mismatches')
    parser.add_argument('--output', action='store_true', help='Output results to CSV file with auto-generated filename')
    parser.add_argument('--output-file', help='Output results to CSV file with specified filename')
    
    args = parser.parse_args()
    
    try:
        # Read CSV file
        df = pd.read_csv(args.csv_file)
        print(f"Successfully loaded {len(df)} issues from {args.csv_file}")
        
        # Calculate match rates
        results, metrics_df = calculate_match_rates(df)
        
        if results:
            # Print results
            print("\n=== MATCH RATE RESULTS ===\n")
            for metric, value in results.items():
                print(f"{metric}: {value}")
            
            # Show detailed breakdown if requested
            if args.detailed:
                print_detailed_breakdown(metrics_df)
            
            # Output results to CSV if requested
            output_file = None
            if args.output:
                # Generate filename based on input CSV and current date/time
                from datetime import datetime
                import os
                
                # Extract base input filename without extension
                input_base = os.path.splitext(os.path.basename(args.csv_file))[0]
                
                # Create timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Create output filename
                output_file = f"{input_base}_match_rates_{timestamp}.csv"
                
            elif args.output_file:
                output_file = args.output_file
                
            if output_file:
                # Convert results to DataFrame for easy CSV export
                results_df = pd.DataFrame([results])
                results_df.to_csv(output_file, index=False)
                print(f"\nResults saved to {output_file}")
                
                # Save the formatted text results to a .txt file
                txt_output_file = output_file.replace('.csv', '.txt')
                with open(txt_output_file, 'w') as f:
                    f.write("=== MATCH RATE RESULTS ===\n\n")
                    for metric, value in results.items():
                        f.write(f"{metric}: {value}\n")
                print(f"Text results saved to {txt_output_file}")
                
                # Also save the detailed metrics DataFrame if detailed output was requested
                if args.detailed:
                    detailed_output = output_file.replace('.csv', '_detailed.csv')
                    metrics_df.to_csv(detailed_output, index=False)
                    print(f"Detailed metrics saved to {detailed_output}")
                    
                    # Save the detailed text breakdown to a detailed .txt file
                    detailed_txt_output = txt_output_file.replace('.txt', '_detailed.txt')
                    with open(detailed_txt_output, 'w') as f:
                        f.write("=== DETAILED BREAKDOWN ===\n\n")
                        
                        # Severity breakdown
                        f.write("SEVERITY MISMATCHES:\n")
                        severity_cross = pd.crosstab(
                            metrics_df['user_severity_std'], 
                            metrics_df['ai_severity_std'],
                            margins=True, 
                            normalize=False
                        )
                        f.write(severity_cross.to_string() + "\n\n")
                        
                        # Occurrence breakdown
                        f.write("OCCURRENCE MISMATCHES:\n")
                        occurrence_cross = pd.crosstab(
                            metrics_df['user_occurrence_std'], 
                            metrics_df['ai_occurrence_std'],
                            margins=True, 
                            normalize=False
                        )
                        f.write(occurrence_cross.to_string() + "\n\n")
                        
                        # Priority breakdown
                        f.write("PRIORITY MISMATCHES:\n")
                        priority_cross = pd.crosstab(
                            metrics_df['user_priority_std'], 
                            metrics_df['ai_priority_std'],
                            margins=True, 
                            normalize=False
                        )
                        f.write(priority_cross.to_string() + "\n")
                    print(f"Detailed text breakdown saved to {detailed_txt_output}")
        else:
            print("Unable to calculate match rates. Please check your CSV format.")
            
    except Exception as e:
        print(f"Error processing CSV file: {e}")

if __name__ == "__main__":
    main()