import os
import pandas as pd
import argparse


def aggregate_csv_files(root_dir):
    all_data = []
    for dir_path, dir_names, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename == 'output-stats.csv':
                file_path = os.path.join(dir_path, filename)
                data = pd.read_csv(file_path)
                data['directory'] = dir_path.split('/', )[-2]  # Add directory path as a column
                all_data.append(data)

    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.rename(columns={'Unnamed: 0': 'measurement'}, inplace=True)
    return combined_df


parser = argparse.ArgumentParser(description='Aggregate result CSV files from multiple directories.')
parser.add_argument('root_dir', type=str, help='Root directory containing subdirectories with CSV files.')
args = parser.parse_args()

aggregated_df = aggregate_csv_files(args.root_dir)
# print(aggregated_df)
# Save dataframe to CSV
aggregated_df.to_csv('aggregated_results.csv', index=False)
