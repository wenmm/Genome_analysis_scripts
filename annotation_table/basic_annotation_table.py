#! python3
# basic_annotation_table
# This program reads in a BLAST-tab file and a list of sequence IDs (can be paired like old\tnew for
# substitution) and formats a basic annotation table that can be extended further with additional
# features

import os, argparse

# Define functions for later use
def validate_args(args):
        # Validate input file locations
        if not os.path.isfile(args.blastTab):
                print('I am unable to locate the input BLAST-tab file (' + args.blastTab + ')')
                print('Make sure you\'ve typed the file name or location correctly and try again.')
                quit()
        elif not os.path.isfile(args.idFile):
                print('I am unable to locate the input ID list file (' + args.idFile + ')')
                print('Make sure you\'ve typed the file name or location correctly and try again.')
                quit()
        elif not os.path.isfile(args.idmappingFile):
                print('I am unable to locate the input idmapping file (' + args.idmappingFile + ')')
                print('Make sure you\'ve typed the file name or location correctly and try again.')
                quit()
        # Validate that numeric arguments are sensible
        if args.evalue < 0:
                print('E-value cannot be less than 0. Specify a positive integer for this value and try again.')
                quit()
        if args.numHits < 1:
                print('Number of hits to return cannot be less than 1. Specify a positive integer for this value and try again.')
                quit()
        # Handle file overwrites
        if os.path.isfile(args.outputFileName):
                print(args.outputFileName + ' already exists. Specify a different output file name or delete, move, or rename this file and run the program again.')
                quit()
        # Check that the database tag argument was provided
        if args.databaseTag == None:
                print('You need to specify a database tag. This value will be presented in the tabular output to note the database that was queried.')
                print('This should be a short descriptive value, such as "UniRef100" or "uniparc"')
                quit()

def parse_idmap(idmapFile):
        idmapSet = set()        # This will simply hold onto values for quick retrieval to see what's inside the idmapping file
        # Load file and iterate through lines
        with open(idmapFile, 'r') as fileIn:
                for line in fileIn:
                        sl = line.split('\t')
                        # Extract information
                        upkbAc = sl[0]
                        uref100Ac = sl[7].split('_', maxsplit=1)[1]
                        upiAc = sl[10]
                        # Save information into a set for quick retrieval
                        idmapSet.add(upkbAc)
                        idmapSet.add(uref100Ac)
                        idmapSet.add(upiAc)
        return idmapSet

def blasttab_best_hits(blastTab, evalue, numHits, idmapSet):
        from itertools import groupby
        # Preliminary declaration of grouper function & main dictionary to hold onto the alignment details of all selected hits
        grouper = lambda x: x.split('\t')[0]
        outDict = {}
        # Iterate through the blastTab file looking at each group of hits to a single query sequence
        with open(blastTab, 'r') as fileIn:
                for key, value in groupby(fileIn, grouper):
                        # Make the group value amenable to multiple iterations, and sort it to present most significant first, least significant last
                        value = list(value)
                        for i in range(len(value)):
                                value[i] = value[i].rstrip('\n').rstrip('\r').split('\t')
                        value.sort(key = lambda x: (float(x[10]),-float(x[11])))        # Sorts by E-value (lowest first) and bitscore (highest first)
                        # Pull out the [X] best hits
                        bestHits = []
                        for val in value:
                                if float(val[10]) <= evalue and len(bestHits) < numHits:
                                        # Alter the target name if it has UniRef prefix
                                        if val[1].startswith('UniRef'):
                                                val[1] = val[1].split('_')[1]           # This handles normal scenarios ("UniRef100_UPI0000") as well as MMseqs2 weird ID handling ("UniRef100_UPI0000_0")
                                        bestHits.append(val)
                        # Skip this hit if we found no matches which pass E-value cut-off
                        if bestHits == []:
                                continue
                        # Dig into the hits and retrieve our best hit which has a mapping in the idmapping file
                        bestMapped = '.'
                        for val in value:
                                if val[1].startswith('UniRef'):
                                        val[1] = val[1].split('_', maxsplit=1)[1]
                                if float(val[10]) <= evalue and val[1] in idmapSet:
                                        bestMapped = val[1] + ' (' + val[10] + ')'
                                        break
                        # Process line to format it for output
                        formattedList = []
                        for i in range(len(bestHits)):
                                if i == 0:
                                        for x in range(1, 12):
                                                formattedList.append([bestHits[i][x]])
                                else:
                                        for x in range(1, 12):
                                                formattedList[x-1].append('[' + bestHits[i][x] + ']')
                        for i in range(len(formattedList)):
                                formattedList[i] = ''.join([formattedList[i][0], ' ', *formattedList[i][1:]])
                        # Add our best mapped value onto the end & save to our outDict
                        outDict[bestHits[0][0]] = formattedList + [bestMapped]
        return outDict

#### USER INPUT SECTION
usage = """This program will read in an input BLAST-tab format file and ID list (either formatted as a newline-separated list of all IDs 
or as a tab-delimited list of old:new ID pairs) and, using an E-value cut-off, produce an abbreviated BLAST-tab-like file with basic 
reformatting of results to enable further expansion. Note that this code is not tested to work with results from BLAST/MMSeqs2 against
the NCBI NR database. When working with the UniRef database, accessions will have the 'UniRef###' prefix stripped - this is why it is 
important to provide an informative database tag so that this information can be reassociated if required.
"""

# Reqs
p = argparse.ArgumentParser(description=usage)
p.add_argument("-inputBlast", "-ib", dest="blastTab",
                   help="Input BLAST-tab file name.")
p.add_argument("-inputID", "-id", dest="idFile",
                   help="Input ID list file name. This can be a simple list of all sequence IDs, or a tab-delimited list containing pairs of old\tnew IDs.")
p.add_argument("-idmappingFile", "-im", dest="idmappingFile",
                   help="Input idmapping_selected.tab file (this is available from the UniProtKB FTP site).")
p.add_argument("-outfile", "-o", dest="outputFileName",
                   help="Output BLAST-tab file name.")
p.add_argument("-evalue", "-e", dest="evalue", type=float,
                   help="E-value significance cut-off (i.e., hits with E-value less significant won't be reported).")
p.add_argument("-numhits", "-n", dest="numHits", type=int,
                   help="Number of hits for each sequence to report (only the most significant will have full alignment details reported).")
p.add_argument("-database", "-db", dest="databaseTag",
                   help="Specify the name of the database being queried (e.g., uniparc or uniref100) - this will be presented in the tabular output.")

args = p.parse_args()
validate_args(args)

# Parse idmapping file
idmapSet = parse_idmap(args.idmappingFile)      # I'd like to use something that isn't so memory demanding (uses 40Gb of mem from personal use) but can't conceive of something suitable and fast.

# Parse the blast-tab file
outDict = blasttab_best_hits(args.blastTab, args.evalue, args.numHits, idmapSet)

# Loop through ID file to rename the genes (if applicable), order the output appropriately, and identify gaps in the BLAST-tab file
with open(args.idFile, 'r') as fileIn, open(args.outputFileName, 'w') as fileOut:
        fileOut.write('#Query\tSource\tTarget_accession\tPercentage_identity\tAlignment_length\tMismatches\tGap_opens\tQuery_start\tQuery_end\tTarget_start\tTarget_end\tExpect_value\tBit_score\tBest_hit_with_idmapping\n')
        for line in fileIn:
                line = line.rstrip('\r\n')
                # Format ID replacement
                if '\t' in line:
                        sl = line.split('\t')
                        oldId = sl[0]
                        newId = sl[1]
                else:
                        oldId = line
                        newId = line
                # Write results to file
                if oldId in outDict:
                        fileOut.write(newId + '\t' + args.databaseTag + '\t' + '\t'.join(outDict[oldId]) + '\n')
                else:
                        fileOut.write(newId + '\t' + 'no_hit' + '\t' + '\t'.join(['.']*12) + '\n')
# Done!
print('Program completed successfully!')