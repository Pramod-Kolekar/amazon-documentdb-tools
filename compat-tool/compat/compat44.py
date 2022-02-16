#!/usr/bin/python3
import os
import sys
import yaml
from mtools.util import logevent
import csv
import json

dollar_file = './compat/dollar.csv'
versions = ['3.6', '4.0']

def all_keys(x):
    k = []
    if (dict == type(x)):
        for kk in x.keys():
            k.append(kk)
            k = k + all_keys(x[kk])
    elif (list == type(x)):
        for vv in x:
            k = k + all_keys(vv)
    return k

def dollar_keys(x):
    return list(set([k for k in all_keys(x) if k.startswith('$')]))

keywords = {}
def load_keywords(fname):
    global keywords
    with open(fname) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')
        for k in reader.fieldnames[1:]:
            if ('Command' == k):
                continue
            keywords[k] = {}
        for row in reader:
            for k in keywords.keys():
                keywords[k][row['Command']] = row[k]
    return keywords

def check_keys(query, usage_map, ver):
    unsupported = False
    for k in dollar_keys(query):
        if k not in keywords[ver]:
            print("new keyword found = {}".format(k))
        elif ('No' == keywords[ver][k]):
            usage_map[k] = usage_map.get(k, 0) + 1
            unsupported = True
    return unsupported

def process_aggregate(logDict, usage_map, ver, lineNum):
    retval = {}
    try:
        #command = yaml.safe_load(" ".join(le.split_tokens[le.split_tokens.index("command:")+2:le.split_tokens.index("planSummary:")]))
        command = logDict['attr']['command']
        p_usage_map = {}
        for p in command["pipeline"]:
            check_keys(p, p_usage_map, ver)
        for k in p_usage_map.keys():
            usage_map[k] = usage_map.get(k, 0) + 1
        actual_query = f'{logDict["attr"]["ns"]}.aggregate({command["pipeline"]})'
        retval = {"unsupported": (0 < len(p_usage_map.keys())), "unsupported_keys": list(p_usage_map.keys()), "logevent": logDict, "processed": 1, "actual_query": actual_query, "exception": False}
    except:
        #print("Unable to parse log line {} | {}".format(lineNum,le))
        retval = {"unsupported": True, "unsupported_keys": [], "logevent": logDict, "processed": 0, "actual_query": "", "exception": True}
    return retval

# //tmc
def process_query(logDict, usage_map, ver, lineNum):
    retval = {}
    p_usage_map = {}
    try:
        #query = yaml.safe_load(le.actual_query)
        query = logDict['attr']['command']
        check_keys(query, p_usage_map, ver)
        for k in p_usage_map.keys():
            usage_map[k] = usage_map.get(k, 0) + 1
        actual_query = f'{logDict["attr"]["ns"]}.find({query["filter"]}'
        if ("projection" in query.keys()):
            actual_query = f'{actual_query}, {query["projection"]}'
        actual_query = f'{actual_query})'
        retval = {"unsupported": (0 < len(p_usage_map.keys())), "unsupported_keys": list(p_usage_map.keys()), "logevent": logDict, "processed": 1, "actual_query": actual_query, "exception": False}
    except:
        #print("Unable to parse log line {} | {}".format(lineNum,le))
        retval = {"unsupported": True, "unsupported_keys": [], "logevent": logDict, "processed": 0, "actual_query": "", "exception": True}
    return retval

def process_find(logDict, usage_map, ver, lineNum):
    retval = {}
    p_usage_map = {}
    try:
        #query = yaml.safe_load(" ".join(le.split_tokens[le.split_tokens.index("command:")+2:le.split_tokens.index("planSummary:")]))
        query = logDict['attr']['command']
        #print('{}'.format(query["filter"]))
        check_keys(query["filter"], p_usage_map, ver)
        for k in p_usage_map.keys():
            usage_map[k] = usage_map.get(k, 0) + 1
        #actual_query = f'{le.namespace}.find({query["filter"]}'
        #actual_query = f'{logDict["attr"]["command"]}.find({query["filter"]}'
        actual_query = f'{logDict["attr"]["ns"]}.find({query["filter"]}'
        if ("projection" in query.keys()):
            actual_query = f'{actual_query}, {query["projection"]}'
        actual_query = f'{actual_query})'
        retval = {"unsupported": (0 < len(p_usage_map.keys())), "unsupported_keys": list(p_usage_map.keys()), "logevent": logDict, "processed": 1, "actual_query": actual_query, "exception": False}
    except:
        #print("Unable to parse log line {} | {}".format(lineNum,le))
        retval = {"unsupported": True, "unsupported_keys": [], "logevent": logDict, "processed": 0, "actual_query": "", "exception": True}
    return retval

# //tmc
def process_update(logDict, usage_map, ver, lineNum):
    retval = {}
    p_usage_map = {}
    try:
        #command = yaml.safe_load(" ".join(le.split_tokens[le.split_tokens.index("command:")+1:le.split_tokens.index("planSummary:")]))
        command = logDict['attr']['command']
        check_keys(command, p_usage_map, ver)
        for k in p_usage_map.keys():
            usage_map[k] = usage_map.get(k, 0) + 1
        actual_query = f'{logDict["attr"]["ns"]}.updateMany({command["q"]}, {command["u"]})'
        retval = {"unsupported": (0 < len(p_usage_map.keys())), "unsupported_keys": list(p_usage_map.keys()), "logevent": logDict, "processed": 1, "actual_query": actual_query, "exception": False}
    except:
        #print("Unable to parse log line {} | {}".format(lineNum,le))
        retval = {"unsupported": True, "unsupported_keys": [], "logevent": logDict, "processed": 0, "actual_query": "", "exception": True}
    return retval

def process_line(logDict, usage_map, ver, cmd_map, lineNum):
    retval = {"unsupported": False, "processed": 0}
    
    #print(f'Command: {le.command}, Component: {le.component}, Actual Query: {le.actual_query}')
    #print('{}'.format(logDict))
    if (logDict['c'] == 'COMMAND'):
        if ('attr' not in logDict) or ('command' not in logDict['attr']):
            pass
            
        elif 'find' in logDict['attr']['command']:
            #print("Processing COMMAND find...")
            #print('{}'.format(logDict))
            retval = process_find(logDict, usage_map, ver, lineNum)
            cmd_map["find"] = cmd_map.get("find", 0) + 1

        elif 'aggregate' in logDict['attr']['command']:
            #print("Processing COMMAND aggregate...")
            #print('{}'.format(logDict))
            retval = process_aggregate(logDict, usage_map, ver, lineNum)
            cmd_map["aggregate"] = cmd_map.get("aggregate", 0) + 1

    elif (logDict['c'] == 'QUERY'):
        #print("Processing query...")
        #print('{}'.format(logDict))
        retval = process_query(logDict, usage_map, ver, lineNum)
        cmd_map["query"] = cmd_map.get("query", 0) + 1

    elif (logDict['c'] == 'WRITE'):
        if ('attr' not in logDict) or ('command' not in logDict['attr']):
            pass
    
        elif ('update' in logDict['attr']['command']):
            #print("Processing update...")
            #print('{}'.format(logDict))
            retval = process_update(logDict, usage_map, ver, lineNum)
            cmd_map["update"] = cmd_map.get("update", 0) + 1

 #   if ("actual_query" in retval.keys()):
 #       print(f'BBB  {retval["actual_query"]}')
        
    return retval

def process_log_file(ver, fname, unsupported_fname, unsupported_query_fname, skipped_line_fname):
    unsupported_file = open(unsupported_fname, "w")
    unsupported_query_file = open(unsupported_query_fname, "w")
    skipped_line_file = open(skipped_line_fname, "w")
    usage_map = {}
    cmd_map = {}
    line_ct = 0
    unsupported_ct = 0
    truncated_line_ct = 0
    unrecognized_line_ct = 0
    parse_exception_ct = 0
    totalLines = 0
    fileArray = []
    if os.path.isfile(fname):
        fileArray.append(fname)
    else:
        for fileName in os.listdir(fname):
            fileArray.append(os.path.join(fname,fileName))
    for thisFile in fileArray:
        print("processing file {}".format(thisFile))
        lineNum = 0
        with open(thisFile) as log_file:
            for line in log_file:
                totalLines += 1
                lineNum += 1
                if (lineNum % 10000 == 0):
                    # display log file progress
                    print(".. line {}".format(lineNum))
                if ("warning: log line attempted" in line) and ("over max size" in line) and ("printing beginning and end" in line):
                    truncated_line_ct += 1
                    skipped_line_file.write("fname = {} | line number = {} | reason = {}\n".format(thisFile,lineNum,"truncated line"))
                else:
                    logDict = json.loads(line)
                    #le = logevent.LogEvent(line)
                    if ("t" not in logDict):
                        unrecognized_line_ct += 1
                        skipped_line_file.write("fname = {} | line number = {} | reason = {}\n".format(thisFile,lineNum,"unrecognized line"))
                        skipped_line_file.write("   Actual Line | {}\n".format(le))
                        #raise SystemExit("Error: <%s> does not appear to be a supported MongoDB log file format" % thisFile)
                    else:
                        pl = process_line(logDict, usage_map, ver, cmd_map, lineNum)
                        line_ct += pl["processed"]
                        #print("{} | {}".format(pl,le))
                        if ("exception" in pl and pl["exception"]):
                            parse_exception_ct += 1
                            skipped_line_file.write("fname = {} | line number = {} | reason = {}\n".format(thisFile,lineNum,"invalid JSON"))
                        elif (pl["unsupported"]):
                            #unsupported_file.write(pl["logevent"].line_str)
                            unsupported_file.write(line)
                            unsupported_file.write("\n")
                            unsupported_query_file.write(f'{pl["actual_query"]}  // {pl["unsupported_keys"]}\n')
                            unsupported_ct += 1
    unsupported_file.close()
    unsupported_query_file.close()
    skipped_line_file.close()

    print("")
    print('Results:')
    print("  Total lines processed = {}".format(totalLines))
    print("")
    if (truncated_line_ct > 0 or unrecognized_line_ct > 0 or parse_exception_ct > 0):
        print("**NOTE** - portions of the log file(s) processed were truncated or incorrectly formatted and excluded from the compatibility assessment")
        print("  Skipped {} log lines due to log line truncation (default 10KB, consider increasing maxLogSizeKB)".format(truncated_line_ct))
        print("  Skipped {} log lines due to unrecognized log format (missing timestamp)".format(unrecognized_line_ct))
        print("  Skipped {} log lines due to unusable log format (invalid JSON)".format(parse_exception_ct))
    print("")

    if (unsupported_ct > 0):
        print(f'{unsupported_ct} out of {line_ct} queries unsupported')
        print(f'Unsupported operators (and number of queries used):')
        for k,v in sorted(usage_map.items(), key=lambda x: (-x[1],x[0])):
            print(f'\t{k:20}  {v}')
    else:
        print('All queries are supported')
    print("")

    print('Query Types:')
    for k,v in sorted(cmd_map.items(), key=lambda x: (-x[1],x[0])):
        print(f'\t{k:10}  {v}')
    print(f'Log lines of unsupported operators logged here: {unsupported_fname}')
    print(f'Queries of unsupported operators logged here: {unsupported_query_fname}')
    print(f'Skipped line information logged here: {skipped_line_fname}')

def print_usage():
    print("Usage: compat.py <version> <input_file or input_file_directory> <output_file>")
    print("  version : " + ", ".join(versions))
    print("  input_file or input_file_directory: location of MongoDB log file or directory containing one or more MongoDB log files")
    print("  output_file: location to write log lines that correspond to unsupported operators")


def main(args):
    if (3 != len(args)):
        print('Incorrect number of arguments')
        print_usage()
        sys.exit()
    ver = args[0]
    if (ver not in versions):
        print(f'Version {ver} not supported')
        print_usage()
        sys.exit()
    infname = args[1]
    if (not os.path.isfile(infname) and not os.path.isdir(infname)):
        print(f'Input file/directory not found ({infname})')
        print_usage()
        sys.exit()
    outfname = args[2]
    outqueryfname = f'{outfname}.query'
    outskippedfname = f'{outfname}.skipped'
    load_keywords(dollar_file)
    process_log_file(ver, infname, outfname, outqueryfname, outskippedfname)
    


if __name__ == '__main__':
    main(sys.argv[1:])
