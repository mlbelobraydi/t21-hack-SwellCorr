from welly import Well, Project
from glob import glob

# # load well data
"""Need to add a method for the user to point to the directory or add additional las files later"""
#w = Well.from_las(str(Path("well_picks/data/las/PoseidonNorth1Decim.LAS"))) #original example

# Get las files
path = 'las/'
print('\n LAS PATH:', path, '\n')
lasfiles = glob(path + '*.LAS')
for fname in lasfiles:
    print(' '*5, fname)
print('\n')



# Get striplog files
path2 = 'tops/'
print('\n STRIP PATH:', path2, '\n')
stripfiles = glob(path2 + '*.csv')
for fname in stripfiles:
    print(' '*5, fname)
print('\n')

p = Project.from_las("las/*.LAS")
well_uwi = [w.uwi for w in p] ##gets the well uwi data for use in the well-selector tool

print(p)