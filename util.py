#import sys 
import os
import subprocess
import json
import threading 
import re
#import pipes
import shutil
import codecs
import string
import random
# from datetime import datetime, date, time

try:
    #python 3
    import MavensMate.config as config
    import MavensMate.lib.apex_extensions as apex_extensions
    from MavensMate.lib.usage_reporter import UsageReporter
    from MavensMate.lib.upgrader import AutomaticUpgrader
    #from MavensMate.lib.printer import PanelPrinter
except BaseException as e:
    print(e)
    #python 2
    import config
    import lib.apex_extensions as apex_extensions
    from lib.usage_reporter import UsageReporter
    from lib.upgrader import AutomaticUpgrader
    #from lib.printer import PanelPrinter

#if os.name != 'nt':
#    import unicodedata

#PLUGIN_DIRECTORY = os.getcwd().replace(os.path.normpath(os.path.join(os.getcwd(), '..', '..')) + os.path.sep, '').replace(os.path.sep, '/')
#for future reference (windows/linux support)
#sublime.packages_path()

import sublime


settings = sublime.load_settings('mavensmate.sublime-settings')
packages_path = sublime.packages_path()
sublime_version = int(float(sublime.version()))

def package_check():
    #ensure user settings are installed
    try:
        if not os.path.exists(packages_path+"/User/mavensmate.sublime-settings"):
            shutil.copyfile(config.mm_dir+"/mavensmate.sublime-settings", packages_path+"/User/mavensmate.sublime-settings")
    except:
        pass

def is_project_legacy():
    if os.path.exists(mm_project_directory()+"/config/settings.yaml"):
        return True
    elif os.path.exists(mm_project_directory()+"/config/.settings"):
        current_settings = parse_json_from_file(mm_project_directory()+"/config/.settings")
        if 'subscription' not in current_settings:
            return True
        else:
            return False

    else:
        return False

def generic_thread_progress_handler(thread, callback, i=0):
    if thread.is_alive():
        sublime.set_timeout(lambda: generic_thread_progress_handler(thread, callback, i), 200)
        return
    else:
        callback(thread.result)
        return
 
# #monitors thread for activity, passes to the result handler when thread is complete
# def thread_progress_handler(operation, threads, printer, i=0):
#     result = None
#     this_thread = None
#     next_threads = []
#     for thread in threads:
#         if printer != None:
#             printer.write('.')
#         if thread.is_alive():
#             next_threads.append(thread)
#             continue
#         if thread.result == None:
#             continue
#         this_thread = thread
#         result = thread.result

#     threads = next_threads

#     if len(threads):
#         sublime.set_timeout(lambda: thread_progress_handler(operation, threads, printer, i), 200)
#         return

#     #handle_result(operation, printer, result, this_thread)

def parse_json_from_file(location):
    try:
        json_data = open(location)
        data = json.load(json_data)
        json_data.close()
        return data
    except:
        return {}

def get_number_of_lines_in_file(file_path):
    f = open(file_path)
    lines = f.readlines()
    f.close()
    return len(lines) + 1

def get_execution_overlays(file_path):
    try:
        response = []
        fileName, ext = os.path.splitext(file_path)
        if ext == ".cls" or ext == ".trigger":
            api_name = fileName.split("/")[-1] 
            overlays = parse_json_from_file(mm_project_directory()+"/config/.overlays")
            for o in overlays:
                if o['API_Name'] == api_name:
                    response.append(o)
        return response
    except:
        return []

#creates resource-bundles for the static resource(s) selected        
def create_resource_bundle(self, files):
    # for file in files:
    #     fileName, fileExtension = os.path.splitext(file)
    #     if fileExtension != '.resource':
    #         sublime.message_dialog("You can only create resource bundles for static resources")
    #         return
    # printer = PanelPrinter.get(self.window.id())
    # printer.show()
    # printer.write('\nCreating Resource Bundle(s)\n')

    # if not os.path.exists(mm_project_directory()+'/resource-bundles'):
    #     os.makedirs(mm_project_directory()+'/resource-bundles')

    # for file in files:
    #     fileName, fileExtension = os.path.splitext(file)
    #     baseFileName = fileName.split("/")[-1]
    #     if os.path.exists(mm_project_directory()+'/resource-bundles/'+baseFileName+fileExtension):
    #         printer.write('[OPERATION FAILED]: The resource bundle already exists\n')
    #         return
    #     cmd = 'unzip \''+file+'\' -d \''+mm_project_directory()+'/resource-bundles/'+baseFileName+fileExtension+'\''
    #     res = os.system(cmd)

    # printer.write('[Resource bundle creation complete]\n')
    # printer.hide()
    # send_usage_statistics('Create Resource Bundle') 
    pass

def get_random_string(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def get_active_file():
    try:
        return sublime.active_window().active_view().file_name()
    except Exception as e:
        return ''

def get_project_name():
    try:
        return os.path.basename(sublime.active_window().folders()[0])
    except:
        return None

def check_for_workspace():
    workspace = mm_workspace()
    if workspace == None or workspace == "":
        #os.makedirs(settings.get('mm_workspace')) we're not creating the directory here bc there's some sort of weird race condition going on
        msg = 'Your [mm_workspace] property is not set. Open \'MavensMate > Settings > User\' or press \'Cmd+Shift+,\' and set this property to the full path of your workspace. Thx!'
        sublime.error_message(msg)  
        raise BaseException

    if not os.path.exists(workspace):
        #os.makedirs(settings.get('mm_workspace')) we're not creating the directory here bc there's some sort of weird race condition going on
        msg = 'Your [mm_workspace] directory \''+workspace+'\' does not exist. Please create the directory then try your operation again. Thx!'
        sublime.error_message(msg)  
        raise BaseException

def sublime_project_file_path():
    project_directory = sublime.active_window().folders()[0]
    if os.path.isfile(project_directory+"/.sublime-project"):
        return project_directory+"/.sublime-project"
    elif os.path.isfile(project_directory+"/"+get_project_name()+".sublime-project"):
        return project_directory+"/"+get_project_name()+".sublime-project"
    else:
        return None 

# check for mavensmate .settings file
def is_mm_project():
    workspace = mm_workspace();
    if workspace == "" or workspace == None or not os.path.exists(workspace):
        return False
    try:
        if os.path.isfile(sublime.active_window().folders()[0]+"/config/.settings"):
            return True
        elif os.path.isfile(sublime.active_window().folders()[0]+"/config/settings.yaml"):
            return True 
        else:
            return False
    except:
        return False

def get_file_extension(filename=None):
    try :
        if not filename: filename = get_active_file()
        fn, ext = os.path.splitext(filename)
        return ext
    except:
        pass
    return None

def get_apex_file_properties():
    return parse_json_from_file(mm_project_directory()+"/config/.apex_file_properties")

def is_mm_file(filename=None):
    try :
        if is_mm_project():
            if not filename: 
                filename = get_active_file()
            if os.path.exists(filename):
                settings = sublime.load_settings('mavensmate.sublime-settings')
                valid_file_extensions = settings.get("mm_apex_file_extensions", [])
                if get_file_extension(filename) in valid_file_extensions:
                    return True
                elif "-meta.xml" in filename:
                    return True
    except:
        pass
    return False

def is_mm_dir(directory):
    if is_mm_project():
        if os.path.isdir(directory):
            if os.path.basename(directory) == "src" or os.path.basename(directory) == get_project_name() or os.path.basename(os.path.abspath(os.path.join(directory, os.pardir))) == "src":
                return True
    return False

def is_browsable_file(filename=None):
    try :
        if is_mm_project():
            if not filename: 
                filename = get_active_file()
            if is_mm_file(filename):
                basename = os.path.basename(filename)
                data = get_apex_file_properties()
                if basename in data:
                    return True
                return os.path.isfile(filename+"-meta.xml")
    except:
        pass
    return False

def is_apex_class_file(filename=None):
    if not filename: filename = get_active_file()
    if is_mm_file(filename): 
        f, ext = os.path.splitext(filename)
        if ext == ".cls":
            return True
    return False

def is_apex_test_file(filename=None):
    if not filename: filename = get_active_file()
    if not is_apex_class_file(filename): return False
    with codecs.open(filename, "r", "utf-8") as content_file:
        content = content_file.read()
        p = re.compile("@isTest\s", re.I + re.M)
        if p.search(content):
            p = re.compile("\stestMethod\s", re.I + re.M)
            if p.search(content): return True
    return False

def mark_overlays(lines):
    mark_line_numbers(lines, "dot", "overlay")

def write_overlays(overlay_result):
    result = json.loads(overlay_result)
    if result["totalSize"] > 0:
        for r in result["records"]:
            sublime.set_timeout(lambda: mark_line_numbers([int(r["Line"])], "dot", "overlay"), 100)

def mark_line_numbers(lines, icon="dot", mark_type="compile_issue"):
    points = [sublime.active_window().active_view().text_point(l - 1, 0) for l in lines]
    regions = [sublime.Region(p, p) for p in points]
    sublime.active_window().active_view().add_regions(mark_type, regions, "operation.fail",
        icon, sublime.HIDDEN | sublime.DRAW_EMPTY)

def clear_marked_line_numbers(mark_type="compile_issue"):
    try:
        sublime.set_timeout(lambda: sublime.active_window().active_view().erase_regions(mark_type), 100)
    except Exception as e:
        print(e.message)
        print('no regions to clean up')


def is_apex_webservice_file(filename=None):
    if not filename: filename = get_active_file()
    if not is_apex_class_file(filename): return False
    with codecs.open(filename, "r", "utf-8") as content_file:
        content = content_file.read()
        p = re.compile("global\s+class\s", re.I + re.M)
        if p.search(content):
            p = re.compile("\swebservice\s", re.I + re.M)
            if p.search(content): return True
    return False

def mm_project_directory():
    #return sublime.active_window().active_view().settings().get('mm_project_directory') #<= bug
    folders = sublime.active_window().folders()
    if len(folders) > 0:
        return sublime.active_window().folders()[0]
    else:
        return mm_workspace()

def mm_workspace():
    settings = sublime.load_settings('mavensmate.sublime-settings')
    if settings.get('mm_workspace') != None:
        workspace = settings.get('mm_workspace')
    else:
        workspace = sublime.active_window().active_view().settings().get('mm_workspace')
    return workspace

def print_debug_panel_message(message):
    # printer = PanelPrinter.get(sublime.active_window().id())
    # printer.show()
    # printer.write(message)
    pass

#preps code completion object for search
def prep_for_search(name): 
    #s1 = re.sub('(.)([A-Z]+)', r'\1_\2', name).strip()
    #return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    #return re.sub('([A-Z])', r'\1_', name)
    return name.replace('_', '')

def get_apex_completions(search_name):
    completions = []
    if not os.path.exists(os.path.join(mm_project_directory(), 'config', '.apex_file_properties')):
        return []

    apex_props = parse_json_from_file(os.path.join(mm_project_directory(), "config", ".apex_file_properties"))

    for p in apex_props.keys():
        if p == search_name+".cls" and 'symbolTable' in apex_props[p]:
            symbol_table = apex_props[p]['symbolTable']
            if 'constructors' in symbol_table:
                for c in symbol_table['constructors']:
                    completions.append((c["visibility"] + " " + c["name"], c["name"]))
            if 'properties' in symbol_table:
                for c in symbol_table['properties']:
                    completions.append((c["visibility"] + " " + c["name"], c["name"]))
            if 'methods' in symbol_table:
                for c in symbol_table['methods']:
                    params = ''
                    if 'parameters' in c and type(c['parameters']) is list and len(c['parameters']) > 0:
                        for p in c['parameters']:
                            params += p['name'] + " (" + p["type"] + ")"
                    completions.append((c["visibility"] + " " + c["name"]+"("+params+") "+c['returnType'], c["name"]))
    return sorted(completions) 

def get_variable_list(view):
    # #print(view.substr(sublime.Region(0,10000000)))
    # if (view.is_dirty()):
    #     view.file_name();
        
    #     thread = MavensMateParserCall(view=view)

    #     #p = subprocess.Popen("java -jar {0} {1}".format(pipes.quote(config.mm_dir+"/bin/parser.jar"), pipes.quote(file_path)), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) 
    #     msg = None
    #     if p.stdout is not None: 
    #         msg = p.stdout.readlines()
    #     elif p.stderr is not None:
    #         msg = p.stdout.readlines() 
    #     if msg == '' or len(msg) == 0:
    #         return_dict = {
    #             "result" : []
    #         }
    #         return json.dumps(return_dict)
    #     else:
    #         result = msg[0].decode("utf-8")
    #         result = result.replace(",]}","]}")
    #         return json.loads(result)
    # else:
    #     view.file_name();
    #     p = subprocess.Popen("java -jar {0} {1}".format(pipes.quote(config.mm_dir+"/bin/parser.jar"), pipes.quote(file_path)), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) 
    #     msg = None
    #     if p.stdout is not None: 
    #         msg = p.stdout.readlines()
    #     elif p.stderr is not None:
    #         msg = p.stdout.readlines() 
    #     if msg == '' or len(msg) == 0:
    #         return_dict = {
    #             "result" : []
    #         }
    #         return json.dumps(return_dict)
    #     else:
    #         result = msg[0].decode("utf-8")
    #         result = result.replace(",]}","]}")
    #         return json.loads(result)
    pass

#parses the input from sublime text
def parse_new_metadata_input(input):
    input = input.replace(" ", "")
    if "," in input:
        params = input.split(",")
        api_name = params[0]
        class_type_or_sobject_name = params[1]
        return api_name, class_type_or_sobject_name
    else:
        return input

def to_bool(value):
    """
       Converts 'something' to boolean. Raises exception for invalid formats
           Possible True  values: 1, True, "1", "TRue", "yes", "y", "t"
           Possible False values: 0, False, None, [], {}, "", "0", "faLse", "no", "n", "f", 0.0, ...
    """
    if str(value).lower() in ("yes", "y", "true",  "t", "1"): return True
    if str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))

def get_tab_file_names():
    tabs = []
    win = sublime.active_window()
    for vw in win.views():
        if vw.file_name() is not None:
            try:
                extension = os.path.splitext(vw.file_name())[1]
                extension = extension.replace(".","")
                if extension in apex_extensions.valid_extensions:
                    tabs.append(vw.file_name())
            except:
                pass
        else:
            pass      # leave new/untitled files (for the moment)
    return tabs 

def send_usage_statistics(action):
    settings = sublime.load_settings('mavensmate.sublime-settings')
    if settings.get('mm_send_usage_statistics') == True:
        sublime.set_timeout(lambda: UsageReporter(action).start(), 3000)

def refresh_active_view():
    sublime.set_timeout(sublime.active_window().active_view().run_command('revert'), 100)

def check_for_updates():
    settings = sublime.load_settings('mavensmate.sublime-settings')
    if settings.get('mm_check_for_updates') == True:
        sublime.set_timeout(lambda: AutomaticUpgrader().start(), 5000)

def start_mavensmate_app():
    p = subprocess.Popen("pgrep -fl \"MavensMate \"", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    msg = None
    if p.stdout is not None: 
        msg = p.stdout.readlines()
    elif p.stderr is not None:
        msg = p.stdout.readlines() 
    if msg == '' or len(msg) == 0:
        settings = sublime.load_settings('mavensmate.sublime-settings')
        if settings != None and settings.get('mm_app_location') != None:
            os.system("open '"+settings.get('mm_app_location')+"'")
        else:
            sublime.error_message("MavensMate is not running, please start it from your Applications folder.")

def finish_update():
    # sublime.message_dialog("MavensMate has been updated successfully!")
    # printer = PanelPrinter.get(sublime.active_window().id())
    # printer.hide()  
    pass  

def get_version_number():
    try:
        json_data = open(config.mm_dir+"/packages.json")
        data = json.load(json_data)
        json_data.close()
        version = data["packages"][0]["platforms"]["osx"][0]["version"]
        return version
    except:
        return ''

class MavensMateParserCall(threading.Thread):
    def __init__(self):
        self.foo = 'bar';

    def run(self):
        pass


