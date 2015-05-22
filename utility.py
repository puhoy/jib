__author__ = 'meatpuppet'

"""http://stackoverflow.com/questions/260273/most-efficient-way-to-search-the-last-x-lines-of-a-file-in-python"""
def tail(fname, n):
    with open(fname, "r") as f:
        f.seek(0, 2)           # Seek @ EOF
        fsize = f.tell()        # Get Size
        f.seek(max (fsize-1024, 0), 0) # Set pos @ last n chars
        lines = f.readlines()       # Read to end
    return lines[-n:]    # Get last n lines