from csv import reader

def structure_prune(k):
    with open('export_2018_08_01-14_28_49.csv') as f:
        export_file_reader = reader(f)
        next(export_file_reader)
        for row in export_file_reader:
            print(row[1:])

structure_prune(0)
