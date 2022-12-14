#!/usr/bin/env python3
"""BiDirectional Sync using rclone"""

__version__ = "V3.2 201201"                         # Version number and date code

#==========================================================================================================
# Configure rclone, including authentication before using this tool.  rclone must be in the search path.
#
# Chris Nelson, November 2017 - 2020
# Contributions:
#   Hildo G. Jr., e2t, kalemas, and silenceleaf
#
# See README.md for revision history
#
# Known bugs:
#   Many print statements use .format vs. Py3 f strings, only for historical reasons.
#
#==========================================================================================================

import argparse
import sys
import re
import os.path
import io
import platform
import shutil
import subprocess
from datetime import datetime
import tempfile
import time
import logging
import inspect                                      # For getting the line number for error messages.
import collections                                  # For dictionary sorting.
import hashlib                                      # For checking if the filter file changed and force --first_sync.
import signal                                       # For keyboard interrupt handler


# Configurations and constants
RCLONE_MIN_VERSION = 1.53
is_Windows = False
is_Linux = False
if sys.platform == "win32":
    is_Windows = True
if sys.platform == "linux":
    is_Linux = True

MAX_DELETE = 50                                     # % deleted allowed, else abort.  Use --force or --max_deletes to override.
CHK_FILE = 'RCLONE_TEST'

RTN_ABORT = 1                                       # Tokens for return codes based on criticality.
RTN_CRITICAL = 2                                    # Aborts allow rerunning.  Criticals block further runs.  See Readme.md.


def bidirSync():

    global path1_lsl_file, path2_lsl_file
    lsl_file_base  = workdir + "LSL_" + (path1_base + path2_base).replace(':','_').replace(r'/','_').replace('\\','_')
            # eg:  '/home/<user>/.rclonesyncwd/LSL_<path1_base><path2_base>'
    path1_lsl_file = lsl_file_base + '_Path1'
    path2_lsl_file = lsl_file_base + '_Path2'

    
    # ***** Check Sync Only *****
    def check_sync():           # Used here and at the end of the flow
        _, path1_contents = load_list(path1_lsl_file)
        _, path2_contents = load_list(path2_lsl_file)

        sync_integrity_fail = False
        for key in path1_contents:
            if key not in path2_contents:
                logging.info(print_msg("ERROR", "Path1 file not found in Path2", key))
                sync_integrity_fail = True
        for key in path2_contents:
            if key not in path1_contents:
                logging.info(print_msg("ERROR", "Path2 file not found in Path1", key))
                sync_integrity_fail = True
        if sync_integrity_fail:
            logging.error("ERROR: The content of Path1 and Path2 are out of sync.  --first-sync required to recover.")
            return 1
        return 0
        
        path1_contents = None
        path2_contents = None

    if args.check_sync_only:
        logging.info(f">>>>> Checking integrity of LSL history files for Path1  <{path1_base}>  versus Path2  <{path2_base}>")
        if check_sync():
            return RTN_CRITICAL
        return 0
    

    logging.info(f"Synching Path1  <{path1_base}>  with Path2  <{path2_base}>")

    args_string = ''
    for arg in sorted(args.__dict__):
        argvalue = getattr(args, arg)
        if type(argvalue) is int:
            argvalue = str(argvalue)
        if type(argvalue) is bool:
            if argvalue is False:
                argvalue = "False"
            else:
                argvalue = "True"
        if type(argvalue) is list:              # --rclone-args case
            rcargs = '=['
            for item in argvalue:
                rcargs += item + ' '
            argvalue = rcargs[:-1] + ']'
        if argvalue is None:
            argvalue = "None"
        args_string += arg + '=' + argvalue + ', '
    logging.info ("Command args: <{}>".format(args_string[:-2]))


    # ***** Handle user_filter_file, if provided *****
    if user_filter_file is not None:
        logging.info("Using filters-file  <{}>".format(user_filter_file))

        if not os.path.exists(user_filter_file):
            logging.error("Specified filters-file file does not exist:  " + user_filter_file)
            return RTN_CRITICAL

        user_filter_file_MD5 = user_filter_file + "-MD5"

        with io.open(user_filter_file, 'rb') as ifile:
            current_file_hash = bytes(hashlib.md5(ifile.read()).hexdigest(), encoding='utf-8')

        stored_file_hash = ''
        if os.path.exists(user_filter_file_MD5):
            with io.open(user_filter_file_MD5, mode="rb") as ifile:
                stored_file_hash = ifile.read()
        elif not first_sync:
            logging.error("MD5 file not found for filters file <{}>.  Must run --first-sync.".format(user_filter_file))
            return RTN_CRITICAL

        if current_file_hash != stored_file_hash and not first_sync:
            logging.error("Filters-file <{}> has chanaged (MD5 does not match).  Must run --first-sync.".format(user_filter_file))
            return RTN_CRITICAL

        if first_sync:
            logging.info("Storing filters-file hash to <{}>".format(user_filter_file_MD5))
            with io.open(user_filter_file_MD5, 'wb') as ofile:
                ofile.write(current_file_hash)


    # ***** Set up --dry-run, and rclone --verbose and --log-format switches *****
    switches = []
    for _ in range(rc_verbose):
        switches.append("-v")
    if dry_run:     # If dry_run, original LSL files are preserved and lsl's are done to the _DRYRUN files.
        switches.append("--dry-run")
        if os.path.exists(path1_lsl_file):
            shutil.copy(path1_lsl_file, path1_lsl_file + '_DRYRUN')
        path1_lsl_file += '_DRYRUN'
        if os.path.exists(path2_lsl_file):          
            shutil.copy(path2_lsl_file, path2_lsl_file + '_DRYRUN')
        path2_lsl_file  += '_DRYRUN'
    if args.no_datetime_log:
        switches.extend(['--log-format', '""'])


    # ***** first_sync generate path1 and path2 file lists, and copy any unique path2 files to path1 ***** 
    if first_sync:
        logging.info(">>>>> --first-sync copying any unique Path2 files to Path1")

        path1_lsl_file_new = path1_lsl_file + '_NEW'
        status, path1_now = get_and_load_lsl ("current Path1", path1_lsl_file_new, path1_base)
        if status:  return status

        path2_lsl_file_new = path2_lsl_file + '_NEW'
        status, path2_now = get_and_load_lsl ("current Path2", path2_lsl_file_new, path2_base)
        if status:  return status

        files_first_sync_copy_P2P1 = []
        for key in path2_now:
            if key not in path1_now:
                logging.info(print_msg("Path2", "  --first-sync queue copy to Path1", key))
                files_first_sync_copy_P2P1.append(key)

        if len(files_first_sync_copy_P2P1) > 0:
            files_first_sync_copy_P2P1_filename = lsl_file_base + "_files_first_sync_copy_P2P1"
            with io.open(files_first_sync_copy_P2P1_filename, mode='wt', encoding='utf8') as outf:
                for item in files_first_sync_copy_P2P1:
                    outf.write(item + "\n")
            logging.info(print_msg("Path2", "  Do queued first-sync copies to", "Path1"))
            if rclone_cmd('copy', path2_base, path1_base, files_file=files_first_sync_copy_P2P1_filename, options=switches):
                return RTN_CRITICAL
            if not args.no_cleanup:
                os.remove(files_first_sync_copy_P2P1_filename)

        
        logging.info(">>>>> --first-sync synching Path1 to Path2")
        # NOTE:  --min-size 0 added to block attempting to overwrite Google Doc files which have size -1 on Google Drive.  180729
        if rclone_cmd('sync', path1_base, path2_base, filter_file=user_filter_file, options=switches + ['--min-size', '0']):
            return RTN_CRITICAL

        logging.info(">>>>> --first-sync refreshing lsl files")
        if rclone_lsl(path1_base, path1_lsl_file, filter_file=user_filter_file):
            return RTN_CRITICAL

        if rclone_lsl(path2_base, path2_lsl_file, filter_file=user_filter_file):
            return RTN_CRITICAL

        if not args.no_cleanup:
            os.remove(path1_lsl_file_new)
            os.remove(path2_lsl_file_new)

        return 0
    

    # ***** Check for existence of prior Path1 and Path2 lsl files *****
    if (not os.path.exists(path1_lsl_file) or not os.path.exists(path2_lsl_file)):
        # On prior critical error abort, the prior LSL files are renamed to _ERROR to lock out further runs
        logging.error("***** Cannot find prior Path1 or Path2 lsl files, likely due to critical error on prior run.")
        return RTN_CRITICAL


    # ***** Check for Path1 deltas relative to the prior sync *****
    logging.info(">>>>> Path1 Checking for Diffs")

    path1_lsl_file_new = path1_lsl_file + '_NEW'
    status, path1_now = get_and_load_lsl ("current Path1", path1_lsl_file_new, path1_base)
    if status:  return status

    def get_check_files (loaded_lsl):
        check_files = {}
        for key in loaded_lsl:
            if args.check_filename in key and "rclonesync/Test/" not in key:
                check_files[key] = loaded_lsl[key]
        return check_files

    if check_access:
        path1_check = get_check_files(path1_now)

    status, path1_prior = get_and_load_lsl ("prior Path1", path1_lsl_file)
    if status:  return status
    path1_prior_count = len(path1_prior)    # Save for later max deletes check

    path1_deltas = {}
    path1_deleted = 0
    path1_found_same = False
    for key in path1_prior:
        _newer=False; _older=False; _size=False; _deleted=False
        if key not in path1_now:
            logging.info(print_msg("Path1", "  File was deleted", key))
            path1_deleted += 1
            _deleted = True
        else:
            if path1_prior[key]['datetime'] != path1_now[key]['datetime']:
                if path1_prior[key]['datetime'] < path1_now[key]['datetime']:
                    logging.info(print_msg("Path1", "  File is newer", key))
                    _newer = True
                else:               # Current path1 version is older than prior sync.
                    logging.info(print_msg("Path1", "  File is OLDER", key))
                    _older = True

        if _newer or _older or _size or _deleted:
            path1_deltas[key] = {'new':False, 'newer':_newer, 'older':_older, 'size':_size, 'deleted':_deleted}
        else:
            path1_found_same = True # Once we've found at least 1 unchanged file we know that not everything has changed, as with a DST time change

    for key in path1_now:
        if key not in path1_prior:
            logging.info(print_msg("Path1", "  File is new", key))
            path1_deltas[key] = {'new':True, 'newer':False, 'older':False, 'size':False, 'deleted':False}

    path1_prior = None              # Free up the memory
    path1_now = None

    path1_deltas = collections.OrderedDict(sorted(path1_deltas.items()))    # Sort the deltas list.
    if len(path1_deltas) > 0:
        news = newers = olders = deletes = 0
        for key in path1_deltas:
            if path1_deltas[key]['new']:      news += 1
            if path1_deltas[key]['newer']:    newers += 1
            if path1_deltas[key]['older']:    olders += 1
            if path1_deltas[key]['deleted']:  deletes += 1
        logging.info(f"  {len(path1_deltas):4} file change(s) on Path1: {news:4} new, {newers:4} newer, {olders:4} older, {deletes:4} deleted")


    # ***** Check for Path2 deltas relative to the prior sync *****
    logging.info(">>>>> Path2 Checking for Diffs")

    path2_lsl_file_new = path2_lsl_file + '_NEW'
    status, path2_now = get_and_load_lsl ("current Path2", path2_lsl_file_new, path2_base)
    if status:  return status

    if check_access:
        path2_check = get_check_files(path2_now)

    status, path2_prior = get_and_load_lsl ("prior Path2", path2_lsl_file)
    if status:  return status
    path2_prior_count = len(path2_prior)    # Save for later max deletes check

    path2_deltas = {}
    path2_deleted = 0
    path2_found_same = False
    for key in path2_prior:
        _newer=False; _older=False; _size=False; _deleted=False
        if key not in path2_now:
            logging.info(print_msg("Path2", "  File was deleted", key))
            path2_deleted += 1
            _deleted = True
        else:
            if path2_prior[key]['datetime'] != path2_now[key]['datetime']:
                if path2_prior[key]['datetime'] < path2_now[key]['datetime']:
                    logging.info(print_msg("Path2", "  File is newer", key))
                    _newer = True
                else:               # Current Path2 version is older than prior sync.
                    logging.info(print_msg("Path2", "  File is OLDER", key))
                    _older = True

        if _newer or _older or _size or _deleted:
            path2_deltas[key] = {'new':False, 'newer':_newer, 'older':_older, 'size':_size, 'deleted':_deleted}
        else:
            path2_found_same = True # Once we've found at least 1 unchanged file we know that not everything has changed, as with a DST time change

    for key in path2_now:
        if key not in path2_prior:
            logging.info(print_msg("Path2", "  File is new", key))
            path2_deltas[key] = {'new':True, 'newer':False, 'older':False, 'size':False, 'deleted':False}

    path2_prior = None              # Free up the memory
    path2_now = None

    path2_deltas = collections.OrderedDict(sorted(path2_deltas.items()))      # Sort the deltas list.
    if len(path2_deltas) > 0:
        news = newers = olders = deletes = 0
        for key in path2_deltas:
            if path2_deltas[key]['new']:      news += 1
            if path2_deltas[key]['newer']:    newers += 1
            if path2_deltas[key]['older']:    olders += 1
            if path2_deltas[key]['deleted']:  deletes += 1
        logging.info(f"  {len(path2_deltas):4} file change(s) on Path2: {news:4} new, {newers:4} newer, {olders:4} older, {deletes:4} deleted")


    # ***** Check access health to the Path1 and Path2 filesystems *****
    if check_access:
        logging.info(">>>>> Checking Path1 and Path2 rclone filesystems access health")

        check_error = False
        if len(path1_check) < 1 or len(path1_check) != len(path2_check):
            logging.error(print_msg("ERROR", "Failed access health test:  <{}> Path1 count {}, Path2 count {}"
                                        .format(chk_file, len(path1_check), len(path2_check)), ""))
            check_error = True

        for key in path1_check:
            if key not in path2_check:
                logging.error(print_msg("ERROR", "Failed access health test:  Path1 key <{}> not found in Path2".format(key), ""))
                check_error = True
        for key in path2_check:
            if key not in path1_check:
                logging.error(print_msg("ERROR", "Failed access health test:  Path2 key <{}> not found in Path1".format(key), ""))
                check_error = True

        if check_error:
            return RTN_CRITICAL

        logging.info(f"  Found <{len(path1_check)}> matching <{args.check_filename}> files on both paths")


    # ***** Check for too many deleted files - possible error condition and don't want to start deleting on the other side !!! *****
    too_many_path1_deletes = False
    if not force and float(path1_deleted)/path1_prior_count > float(max_deletes)/100:
        logging.error("SAFETY ABORT - Excessive number of deletes (>{}%, {} of {}) found on the Path1 filesystem <{}>.  Run with --force if desired."
                       .format(max_deletes, path1_deleted, path1_prior_count, path1_base))
        too_many_path1_deletes = True

    too_many_path2_deletes = False
    if not force and float(path2_deleted)/path2_prior_count > float(max_deletes)/100:
        logging.error("SAFETY ABORT - Excessive number of deletes (>{}%, {} of {}) found on the Path2 filesystem <{}>.  Run with --force if desired."
                       .format(max_deletes, path2_deleted, path2_prior_count, path2_base))
        too_many_path2_deletes = True

    if too_many_path1_deletes or too_many_path2_deletes:
        return RTN_ABORT


    # ***** Check for all files changed, such as all dates changed due to DST change, to avoid errant copy everything.  See README.md. *****
    if not force and not path1_found_same:
        logging.error(f"SAFETY ABORT - All files were found to be changed on the Path1 filesystem <{path1_base}>.  Something is possibly wrong.  Run with --force if desired.")
        return RTN_ABORT
        
    if not force and not path2_found_same:
        logging.error(f"SAFETY ABORT - All files were found to be changed on the Path2 filesystem <{path2_base}>.  Something is possibly wrong.  Run with --force if desired.")
        return RTN_ABORT
        

    # ***** Determine and apply changes to Path1 and Path2 *****
    files_copy_P1P2 = []
    files_copy_P2P1 = []
    files_delete_P1 = []
    files_delete_P2 = []
    already_handled = {}

    if len(path1_deltas) == 0 and len(path2_deltas) == 0:
        logging.info(">>>>> No changes on Path1 or Path2")
    else:
        logging.info(">>>>> Determining and applying changes")

        for key in path1_deltas:
            if path1_deltas[key]['new'] or path1_deltas[key]['newer'] or path1_deltas[key]['older']:
                if key not in path2_deltas:
                    logging.info(print_msg("Path1", "  Queue copy to Path2", path2_base + key))
                    files_copy_P1P2.append(key)

                elif path2_deltas[key]['deleted']:
                    logging.info(print_msg("Path1", "  Queue copy to Path2", path2_base + key))
                    files_copy_P1P2.append(key)
                    already_handled[key] = 1

                elif path2_deltas[key]['new'] or path2_deltas[key]['newer'] or path2_deltas[key]['older']:
                    logging.warning(print_msg("WARNING", "  New or changed in both paths", key))
                    logging.warning(print_msg("Path1", "  Renaming Path1 copy", path1_base + key + "_Path1"))
                    if rclone_cmd('moveto', path1_base + key, path1_base + key + "_Path1", options=switches):
                        return RTN_CRITICAL
                    logging.warning(print_msg("Path1", "  Queue copy to Path2", path2_base + key + "_Path1"))
                    files_copy_P1P2.append(key + "_Path1")

                    logging.warning(print_msg("Path2", "  Renaming Path2 copy", path2_base + key + "_Path2"))
                    if rclone_cmd('moveto', path2_base + key, path2_base + key + "_Path2", options=switches):
                        return RTN_CRITICAL
                    logging.warning(print_msg("Path2", "  Queue copy to Path1", path1_base + key + "_Path2"))
                    files_copy_P2P1.append(key + "_Path2")
                    already_handled[key] = 1

            else: # Path1 deleted
                if key not in path2_deltas:
                    logging.info(print_msg("Path2", "  Queue delete", path2_base + key))
                    files_delete_P2.append(key)
                elif path2_deltas[key]['new'] or path2_deltas[key]['newer'] or path2_deltas[key]['older']:
                    logging.info(print_msg("Path2", "  Queue copy to Path1", path1_base + key))
                    files_copy_P2P1.append(key)
                    already_handled[key] = 1
                elif path2_deltas[key]['deleted']:
                    already_handled[key] = 1

        for key in path2_deltas:
            if key not in already_handled:
                if path2_deltas[key]['new'] or path2_deltas[key]['newer'] or path2_deltas[key]['older']:
                    logging.info(print_msg("Path2", "  Queue copy to Path1", path1_base + key))
                    files_copy_P2P1.append(key)
                else: # Deleted 
                    logging.info(print_msg("Path1", "  Queue delete", path1_base + key))
                    files_delete_P1.append(key)

        path1_changes = False
        path2_changes = False
        # Do the batch operation
        if len(files_copy_P2P1) > 0:
            path1_changes = True
            files_copy_P2P1_filename = lsl_file_base + "_files_copy_P2P1"
            with io.open(files_copy_P2P1_filename, mode='wt', encoding='utf8') as outf:
                for item in files_copy_P2P1:
                    outf.write(item + "\n")
            logging.info(print_msg("Path2", "  Do queued copies to", "Path1"))
            if rclone_cmd('copy', path2_base, path1_base, files_file=files_copy_P2P1_filename, options=switches):
                return RTN_CRITICAL
            if not args.no_cleanup:
                os.remove(files_copy_P2P1_filename)

        if len(files_copy_P1P2) > 0:
            path2_changes = True
            files_copy_P1P2_filename = lsl_file_base + "_files_copy_P1P2"
            with io.open(files_copy_P1P2_filename, mode='wt', encoding='utf8') as outf:
                for item in files_copy_P1P2:
                    outf.write(item + "\n")
            logging.info(print_msg("Path1", "  Do queued copies to", "Path2"))
            if rclone_cmd('copy', path1_base, path2_base, files_file=files_copy_P1P2_filename, options=switches):
                return RTN_CRITICAL
            if not args.no_cleanup:
                os.remove(files_copy_P1P2_filename)

        if len(files_delete_P1) > 0:
            path1_changes = True
            files_delete_P1_filename = lsl_file_base + "_files_delete_P1"
            with io.open(files_delete_P1_filename, mode='wt', encoding='utf8') as outf:
                for item in files_delete_P1:
                    outf.write(item + "\n")
            logging.info(print_msg("", "  Do queued deletes on", "Path1"))
            if rclone_cmd('delete', path1_base, files_file=files_delete_P1_filename, options=switches):
                return RTN_CRITICAL
            if not args.no_cleanup:
                os.remove(files_delete_P1_filename)

        if len(files_delete_P2) > 0:
            path2_changes = True
            files_delete_P2_filename = lsl_file_base + "_files_delete_P2"
            with io.open(files_delete_P2_filename, mode='wt', encoding='utf8') as outf:
                for item in files_delete_P2:
                    outf.write(item + "\n")
            logging.info(print_msg("", "  Do queued deletes on", "Path2"))
            if rclone_cmd('delete', path2_base, files_file=files_delete_P2_filename, options=switches):
                return RTN_CRITICAL
            if not args.no_cleanup:
                os.remove(files_delete_P2_filename)

        files_copy_P1P2 = None      # Free up the memory
        files_copy_P2P1 = None
        files_delete_P1 = None
        files_delete_P2 = None
        already_handled = None


    # ***** Clean up and check LSL files integrity *****
    logging.info(">>>>> Refreshing Path1 and Path2 lsl files")
    if len(path1_deltas) == 0 and len(path2_deltas) == 0:
        shutil.copy2(path1_lsl_file_new, path1_lsl_file)
        shutil.copy2(path2_lsl_file_new, path2_lsl_file)
    else:
        if path1_changes:
            if rclone_lsl(path1_base, path1_lsl_file, filter_file=user_filter_file):
                return RTN_CRITICAL
        else:
            shutil.copy2(path1_lsl_file_new, path1_lsl_file)

        if path2_changes:
            if rclone_lsl(path2_base, path2_lsl_file, filter_file=user_filter_file):
                return RTN_CRITICAL
        else:
            shutil.copy2(path2_lsl_file_new, path2_lsl_file)

    if not args.no_cleanup:
        os.remove(path1_lsl_file_new)
        os.remove(path2_lsl_file_new)

    path1_deltas    = None      # Free up the memory
    path2_deltas    = None

    if not args.no_check_sync and not dry_run:
        logging.info(f">>>>> Checking integrity of LSL history files for Path1  <{path1_base}>  versus Path2  <{path2_base}>")
        if check_sync():
            return RTN_CRITICAL


    # ***** Optional rmdirs for empty directories *****
    if rmdirs:
        logging.info(">>>>> rmdirs Path1")
        if rclone_cmd('rmdirs', path1_base, filter_file=user_filter_file, options=switches):
            return RTN_CRITICAL

        logging.info(">>>>> rmdirs Path2")
        if rclone_cmd('rmdirs', path2_base, filter_file=user_filter_file, options=switches):
            return RTN_CRITICAL

    return 0


# =====  Support functions  ==========================================================
def print_msg(tag, msg, key=''):
    return "  {:9}{:35} - {}".format(tag, msg, key)


# ***** rclone call wrapper functions with retries *****
MAXTRIES=3
def rclone_lsl(path, ofile, filter_file=None, options=None):
    """
    Fetch an rclone LSL of the path and write it to ofile.
    filter_file is a string full path to a file which will be passed to rclone --filter-from.
    options is a list of switches passed to rclone (not currently used)
    """
    linenum = inspect.getframeinfo(inspect.stack()[1][0]).lineno
    process_args = [rclone, "lsl", path, "--config", rcconfig]
    if filter_file is not None:
        process_args.extend(["--filter-from", filter_file])
    if options is not None:
        process_args.extend(options)
    if args.rclone_args is not None:
        process_args.extend(args.rclone_args)
    logging.debug("    rclone command:  {}".format(process_args))
    for x in range(MAXTRIES):
        with io.open(ofile, "wt", encoding='utf8') as of:
            if not subprocess.call(process_args, stdout=of):
                return 0
            logging.info(print_msg("WARNING", "rclone lsl try {} failed.".format(x+1)))
    logging.error(print_msg("ERROR", "rclone lsl failed.  Specified path invalid?  (Line {})".format(linenum)))
    return 1


def rclone_cmd(cmd, p1=None, p2=None, filter_file=None, files_file=None, options=None):
    """
    Execute an rclone command.
    p1 and p2 are optional.
    filter_file is a string full path to a file which will be passed to rclone --filter-from.
    files_file is a string full path to a list of files for the rclone command operation, such as copy these files.
    options is a list of switches passed to rclone
        EG: ["--filter-from", "some_file", "--dry-run", "-vv", '--log-format', '""']
    """
    linenum = inspect.getframeinfo(inspect.stack()[1][0]).lineno
    process_args = [rclone, cmd, "--config", rcconfig]
    if p1 is not None:
        process_args.append(p1)
    if p2 is not None:
        process_args.append(p2)
    if filter_file is not None:
        process_args.extend(["--filter-from", filter_file])
    if files_file is not None:
        process_args.extend(["--files-from-raw", files_file])
    if options is not None:
        process_args.extend(options)
    if args.rclone_args is not None:
        process_args.extend(args.rclone_args)
    logging.debug("    rclone command:  {}".format(process_args))
    for x in range(MAXTRIES):
        try:
            p = subprocess.Popen(process_args)
            p.wait()
            if p.returncode == 0:
                return 0
        except Exception as e:
            logging.info(print_msg("WARNING", "rclone {} try {} failed.".format(cmd, x+1), p1))
            logging.info("message:  <{}>".format(e))
    logging.error(print_msg("ERROR", "rclone {} failed.  (Line {})".format(cmd, linenum), p1))
    return 1


LINE_FORMAT = re.compile(r'\s*([0-9]+) ([\d\-]+) ([\d:]+).([\d]+) (.*)')
def load_list(lslfile):
    """
    Load the content of the lslfile into a dictionary.
    The key is the path to the file relative to the Path1/Path2 base.
    File size of -1, as for Google Docs files, prints a warning and are not loaded.
    lsl file format example:
          size <----- datetime (epoch) ----> key
       3009805 2013-09-16 04:13:50.000000000 12 - Wait.mp3
        541087 2017-06-19 21:23:28.610000000 DSC02478.JPG
    Returned sorted dictionary structure:
        OrderedDict([('RCLONE_TEST', {'size': '110', 'datetime': 946710000.0}),
                     ('file1.txt', {'size': '0', 'datetime': 946710000.0}), ...
    """
    d = {}
    try:
        line = "<none>"
        line_cnt = 0
        with io.open(lslfile, mode='rt', encoding='utf8') as f:
            for line in f:
                line_cnt += 1
                out = LINE_FORMAT.match(line)
                if out:
                    size = out.group(1)
                    date = out.group(2)
                    _time = out.group(3)
                    microsec = out.group(4)
                    date_time = time.mktime(datetime.strptime(date + ' ' + _time, '%Y-%m-%d %H:%M:%S').timetuple()) + float('.'+ microsec)
                    filename = out.group(5)
                    if filename in d:
                        logging.warning (f"WARNING  Duplicate line in LSL file:   <{line[:-1]}>")
                        strtime = datetime.fromtimestamp(d[filename]['datetime']).strftime("%Y-%m-%d %H:%M:%S.%f")
                        logging.warning (f"         Prior found (keeping latest): <{d[filename]['size']:>9} {strtime}    {filename}>")
                        if date_time > d[filename]['datetime']:
                            d[filename] = {'size': size, 'datetime': date_time}
                    else:
                        d[filename] = {'size': size, 'datetime': date_time}

                else:
                    logging.warning("Something wrong with this line (ignored) in {}.  (Google Doc files cannot be synced.):\n   <{}>".format(lslfile, line))
        return 0, collections.OrderedDict(sorted(d.items()))        # return Success and a sorted list

    except Exception as e:
        logging.error(f"Exception in load_list loading <{lslfile}>:\n  <{e}>\n  Line # {line_cnt}:  {line}")
        return 1, ""                                                # return False


def get_and_load_lsl (path_text, lsl_file, path12=None):
    """
    Optionally call for an rclone lsl of the referenced path12, written to the lsl_file.
    Then load the lsl file content into into a dictionary and return the dictionary to the caller.
    path_text is a convenience string for logging, eg "Path2 prior"
    lsl_file is the full path string for file to be written to by the rclone lsl, and read from for loading the content.
    path12 is a string to be passed to the rclone lsl, eg "Dropbox:"
    """
    if path12 is not None:
        if rclone_lsl(path12, lsl_file, filter_file=user_filter_file):
            return RTN_ABORT, None
    status, loaded_list = load_list(lsl_file)
    if status:
        logging.error(print_msg("ERROR", f"Failed loading {path_text} list file <{lsl_file}>"))
        return RTN_ABORT, None
    if not first_sync and len(loaded_list) == 0:
        logging.error(print_msg("ERROR", f"Zero length in {path_text} list file <{lsl_file}>.  Cannot sync to an empty directory tree."))
        return RTN_CRITICAL, None
    return 0, loaded_list


def request_lock(caller, lock_file):
    for _ in range(5):
        if os.path.exists(lock_file):
            with io.open(lock_file, mode='rt', encoding='utf8',errors="replace") as fd:
                locked_by = fd.read()
                logging.info("Lock file exists - Waiting a sec: <{}>\n<{}>".format(lock_file, locked_by[:-1]))   # remove the \n
            time.sleep(1)
        else:  
            with io.open(lock_file, mode='wt', encoding='utf8') as fd:
                fd.write("Locked by {} at {}\n".format(caller, time.asctime(time.localtime())))
                logging.info("Lock file created: <{}>".format(lock_file))
            return 0
    logging.warning("Timed out waiting for lock file to be cleared: <{}>".format(lock_file))
    return -1

def release_lock(lock_file):
    if os.path.exists(lock_file):
        logging.info("Lock file removed: <{}>".format(lock_file))
        os.remove(lock_file)
        return 0
    else:
        logging.warning("Attempted to remove lock file but the file does not exist: <{}>".format(lock_file))
        return -1

def keyboardInterruptHandler(signal, frame):
    logging.error("***** KeyboardInterrupt Critical Error Abort - Must run --first-sync to recover.  See README.md *****\n")
    if os.path.exists(path2_lsl_file):
        shutil.move(path2_lsl_file, path2_lsl_file + '_ERROR')
    if os.path.exists(path1_lsl_file):
        shutil.move(path1_lsl_file, path1_lsl_file + '_ERROR')
    release_lock(lock_file)
    sys.exit(2)
signal.signal(signal.SIGINT, keyboardInterruptHandler)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="***** BiDirectional Sync for Cloud Services using rclone *****")
    parser.add_argument('Path1',
                        help="Local path, or cloud service with ':' plus optional path.  Type 'rclone listremotes' for list of configured remotes.")
    parser.add_argument('Path2',
                        help="Local path, or cloud service with ':' plus optional path.  Type 'rclone listremotes' for list of configured remotes.")
    parser.add_argument('-1', '--first-sync', action='store_true',
                        help="First run setup.  WARNING: Path1 files may overwrite path2 versions.  Consider using with --dry-run first.  Also asserts --verbose.")
    parser.add_argument('-c', '--check-access', action='store_true',
                        help="Ensure expected RCLONE_TEST files are found on both path1 and path2 filesystems, else abort.")
    parser.add_argument('--check-filename', default=CHK_FILE, 
                        help=f"Filename for --check-access (default is <{CHK_FILE}>).")
    parser.add_argument('-D', '--max-deletes', type=int, default=MAX_DELETE,
                        help=f"Safety check for percent maximum deletes allowed (default {MAX_DELETE}%%).  If exceeded the rclonesync run will abort.  See --force.")
    parser.add_argument('-F', '--force', action='store_true',
                        help="Bypass --max-deletes safety check and run the sync.  Also asserts --verbose.")
    parser.add_argument('--no-check-sync', action='store_true',
                        help="Disable comparison of final LSL files (default is check-sync enabled).")
    parser.add_argument('--check-sync-only', action='store_true',
                        help="Only execute the comparison of LSL files from the last rclonesync run.")
    parser.add_argument('-e', '--remove-empty-directories', action='store_true',
                        help="Execute rclone rmdirs as a final cleanup step.")
    parser.add_argument('-f','--filters-file', default=None,
                        help="File containing rclone file/path filters (needed for Dropbox).")
    parser.add_argument('-r','--rclone', default="rclone",
                        help="Path to rclone executable (default is rclone in path environment var).")
    parser.add_argument('--config', default=None,
                        help="Path to rclone config file (default is typically ~/.config/rclone/rclone.conf).")
    parser.add_argument('--rclone-args', nargs=argparse.REMAINDER,
                        help="Optional argument(s) to be passed to rclone.  Specify this switch and rclone ags at the end of rclonesync command line.")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Enable event logging with per-file details.  Specify once for info and twice for debug detail.")
    parser.add_argument('--rc-verbose', action='count',
                        help="Enable rclone's verbosity levels (May be specified more than once for more details.  Also asserts --verbose.)")
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help="Go thru the motions - No files are copied/deleted.  Also asserts --verbose.")
    parser.add_argument('-w', '--workdir', default=os.path.expanduser("~/.rclonesyncwd"),
                        help="Specified working dir - useful for testing.  Default is ~user/.rclonesyncwd.")
    parser.add_argument('--no-datetime-log', action='store_true',
                        help="Disable date-time from log output - useful for testing.")
    parser.add_argument('--no-cleanup', action='store_true',
                        help="Retain working files - useful for debug and testing.")
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__,
                        help="Return rclonesync's version number and exit.")
    args = parser.parse_args()
    
    first_sync   =  args.first_sync
    check_access =  args.check_access
    chk_file     =  args.check_filename
    max_deletes  =  args.max_deletes
    verbose      =  args.verbose
    rc_verbose   =  args.rc_verbose
    if rc_verbose == None: rc_verbose = 0
    user_filter_file =  args.filters_file
    rclone       =  args.rclone
    dry_run      =  args.dry_run
    force        =  args.force
    rmdirs       =  args.remove_empty_directories


    # Set up logging
    if not args.no_datetime_log:
        logging.basicConfig(format='%(asctime)s:  %(message)s') # /%(levelname)s/%(module)s/%(funcName)s
    else:
        logging.basicConfig(format='%(message)s')

    if verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)             # Log debug detail
    elif verbose>0 or rc_verbose>0 or force or first_sync or dry_run:
        logging.getLogger().setLevel(logging.INFO)              # Log each file transaction
    else:
        logging.getLogger().setLevel(logging.WARNING)           # Log only unusual events.  Normally silent.

    logging.info(f"***** BiDirectional Sync for Cloud Services using rclone ({__version__}) *****")


    # Environment checks
    if is_Windows:
        chcp = subprocess.check_output(["chcp"], shell=True).decode("utf-8")
        err = False
        py_encode_env = ''
        if "PYTHONIOENCODING" in os.environ:
            py_encode_env = os.environ["PYTHONIOENCODING"]
        if "65001" not in chcp:
            logging.error ("ERROR  In the Windows CMD shell execute <chcp 65001> to enable support for UTF-8.")
            err = True
        if py_encode_env.lower().replace('-','') != "utf8":
            logging.error ("ERROR  In the Windows CMD shell execute <set PYTHONIOENCODING=UTF-8> to enable support for UTF-8.")
            err = True
        if err:
            sys.exit(1)


    # Check workdir goodness
    workdir = args.workdir
    if not (workdir.endswith('/') or workdir.endswith('\\')):   # 2nd check is for Windows paths
        workdir += '/'
    try:
        if not os.path.exists(workdir):
            os.makedirs(workdir)
    except Exception as e:
        logging.error(f"ERROR  Cannot access workdir at <{workdir}>.")
        sys.exit(1)


    # Check rclone related goodness
    rcversion_FORMAT = re.compile(r"v?(\d+)\.(\d+).*")
    try:
        rclone_V = subprocess.check_output([rclone, "version"]).decode("utf8").split()[1]
    except Exception as e:
        logging.error(f"ERROR  Cannot invoke <rclone version>.  rclone not installed or invalid --rclone path?\nError message: {e}.\n")
        sys.exit(1)
    out = rcversion_FORMAT.match(rclone_V)
    if out:
        rcversion = int(out.group(1)) + float("0." + out.group(2))
        if rcversion < RCLONE_MIN_VERSION:
            logging.error(f"ERROR  rclone minimum version is v{RCLONE_MIN_VERSION}.  Found version v{rcversion}.")
            sys.exit(1)
    else:
        logging.error(f"ERROR  Cannot get rclone version info.  Check rclone installation - minimum version v{RCLONE_MIN_VERSION}.")
        sys.exit(1)

    rcconfig = args.config
    if rcconfig is None:
        try:  # Extract the second line from the two line <rclone config file> output similar to:
                # Configuration file is stored at:
                # /home/<me>/.config/rclone/rclone.conf
            rcconfig = str(subprocess.check_output([rclone, "config", "file"]).decode("utf8")).split(':\n')[1].strip()
        except Exception as e:
            logging.error(f"ERROR  Cannot get <rclone config file> path.  rclone install problem?\nError message: {e}.\n")
            sys.exit(1)
    if not os.path.exists(rcconfig):
        logging.error(f"ERROR  rclone config file <{rcconfig}> not found.  Check rclone configuration, or invalid --config switch?")
        sys.exit(1)

    try:
        clouds = subprocess.check_output([rclone, "listremotes", "--config", rcconfig]).decode("utf8") .split("\n")[:-1]
    except Exception as e:
        logging.error("ERROR  Cannot get list of known remotes.  Have you run rclone config?")
        sys.exit(1)


    # Set up Path1 / Path2
    def pathparse(path):
        """Handle variations in a path argument.
        Cloud:              - Root of the defined cloud
        Cloud:some/path     - Supported with our without path leading '/'s
        X:                  - Windows drive letter
        X:\\some\\path      - Windows drive letter with absolute or relative path
        some/path           - Relative path from cwd (and on current drive on Windows)
        //server/path       - UNC paths are supported
        On Windows a one-character cloud name is not supported - it will be interprested as a drive letter.
        """
        _cloud = False
        path_base = ''
        if ':' in path:
            if len(path) == 1:                                  # Handle corner case of ':' only passed in
                logging.error("ERROR  Path argument <{}> not a legal path.".format(path))
                sys.exit(1)
            if path[1] == ':' and is_Windows:                   # Windows drive letter case
                path_base = path
                if not path_base.endswith('\\'):                # For consistency ensure the path ends with '/'
                    path_base += '/'
            else:                                               # Cloud case with optional path part
                # path_FORMAT = re.compile(r'([\w-]+):(.*)')
                path_FORMAT = re.compile(r'([ \w-]+):(.*)')
                out = path_FORMAT.match(path)
                if out:
                    _cloud = True
                    cloud_name = out.group(1) + ':'
                    if cloud_name not in clouds:
                        logging.error(f"ERROR  Path argument <{cloud_name}> not in list of configured Clouds: {clouds}.")
                        sys.exit(1)
                    path_part = out.group(2)
                    if path_part:
                        if not (path_part.endswith('/') or path_part.endswith('\\')):    # 2nd check is for Windows paths
                            path_part += '/'
                    path_base = cloud_name + path_part
        else:                                                   # Local path (without Windows drive letter)
            path_base = path
            if not (path_base.endswith('/') or path_base.endswith('\\')):
                path_base += '/'

        if not _cloud:
            if not os.path.exists(path_base):
                logging.error(f"ERROR  Local path parameter <{path_base}> cannot be accessed.  Path error?")
                sys.exit(1)

        return path_base

    path1_base = pathparse(args.Path1)
    path2_base = pathparse(args.Path2)

    # Run the job
    lock_file = os.path.join(tempfile.gettempdir(), 'rclonesync_LOCK_' + (
        path1_base + path2_base).replace(':','_').replace(r'/','_').replace('\\','_'))

    if request_lock(sys.argv, lock_file) == 0:
        status = bidirSync()
        release_lock(lock_file)
        if status == RTN_CRITICAL:
            logging.error("***** Critical Error Abort - Must run --first-sync to recover.  See README.md *****\n")
            if os.path.exists(path2_lsl_file):
                shutil.move(path2_lsl_file, path2_lsl_file + '_ERROR')
            if os.path.exists(path1_lsl_file):
                shutil.move(path1_lsl_file, path1_lsl_file + '_ERROR')
            sys.exit(2)
        if status == RTN_ABORT:
            logging.error("***** Error Abort.  Try running rclonesync again. *****\n")
            sys.exit(1)
        if status == 0:
            logging.info(">>>>> Successful run.  All done.\n")
            sys.exit(0)
    else:
        logging.warning("***** Prior lock file in place, aborting.  Try running rclonesync again. *****\n")
        sys.exit(1)
