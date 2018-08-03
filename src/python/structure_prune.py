from csv import reader

def structure_prune(k):
    with open('export_2018_08_01-14_28_49.csv') as f:
        export_file_reader = reader(f)
        for row in export_file_reader:
            print(row)

structure_prune(0)
