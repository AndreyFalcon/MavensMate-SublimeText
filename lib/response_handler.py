import sublime
import json
import os
import sys
import html.parser
import traceback
from .merge import MavensMateDiffThread
import MavensMate.util as util
import MavensMate.config as config
sublime_version = int(float(sublime.version()))
settings = sublime.load_settings('mavensmate.sublime-settings')
html_parser = html.parser.HTMLParser()
debug = config.debug

class MavensMateResponseHandler(object):

    def __init__(self, context):
        self.operation           = context.get('operation', None)
        self.process_id          = context.get('process_id', None)
        self.printer             = context.get('printer', None)
        self.thread              = context.get('thread', None)
        self.response            = context.get('response', None)
        self.process_region      = self.printer.panel.find(self.process_id,0)
        self.status_region       = self.printer.panel.find('   Result: ',self.process_region.begin())

        try:
            self.response = json.loads(self.response)
            self.result = self.response['result']
        except:
            debug('Could not load json response from mavensmate')
            debug(self.response)
            pass

    def has_error(self):
        return 'error' in self.response

    def execute(self):
        if self.response is None:
            self.__print_to_panel('[OPERATION FAILED]: No response from mavensmate executable. Please enable logging (http://mavensmate.com/Plugins/Sublime_Text/Plugin_Logging) and post relevant log(s) to a new issue at https://github.com/joeferraro/MavensMate-SublimeText')
        elif self.has_error():
            self.__print_error()
        else:
            try:
                if self.operation == 'compile-metadata' or self.operation == 'compile-project':
                    self.__handle_compile_response()
                elif self.operation == 'run-tests' or self.operation == 'run-all-tests':
                    self.__handle_test_result()
                elif self.operation == 'run-apex-script':
                    self.__handle_apex_script_result()
                elif self.operation == 'get-coverage':
                    self.__handle_coverage_result()
                elif self.operation == 'coverage-report':
                    self.__handle_coverage_report_result()
                elif self.operation == 'get-org-wide-test-coverage':
                    self.__handle_org_wide_coverage_result()
                elif self.operation == 'delete-metadata':
                    self.__handle_delete_metadata_result()
                else:
                    self.__handle_generic_command_result()
            except Exception as e:
                debug(e)
                debug(traceback.print_exc())
                self.__print_result()

            self.__finish()

    def __finish(self):
        try:
            if self.operation == 'refresh':
                sublime.set_timeout(lambda: sublime.active_window().active_view().run_command('revert'), 200)
                util.clear_marked_line_numbers()
        except:
            pass #TODO

    def __print_error(self):
        msg = '[ERROR]: '+self.response.error
        if self.response.stack is not None:
            msg += '\n\n' + self.response.stack
        self.__print_to_panel(msg)

    def __print_to_panel(self, msg):
        self.printer.panel.run_command('write_operation_status', {'text': msg, 'region': self.__get_print_region() })

    def __get_print_region(self):
        return [self.status_region.end(), self.status_region.end()+10]

    def __print_result(self):
        msg = ''
        if type(self.response) is dict and 'body' in self.response:
           msg += '[RESPONSE FROM MAVENSMATE]: '+self.response['body']
        elif self.response != None and self.response != "" and (type(self.response) is str or type(self.response) is bytes):
            msg += '[OPERATION FAILED]: Whoops, unable to parse the response. Please enable logging (http://mavensmate.com/Plugins/Sublime_Text/Plugin_Logging) and post relevant log(s) to a new issue at https://github.com/joeferraro/MavensMate-SublimeText\n'
            msg += '[RESPONSE FROM MAVENSMATE]: '+self.response
        else:
            msg += '[OPERATION FAILED]: Whoops, unable to parse the response. Please enable logging (http://mavensmate.com/Plugins/Sublime_Text/Plugin_Logging) and post relevant log(s) to a new issue at https://github.com/joeferraro/MavensMate-SublimeText\n'
            msg += '[RESPONSE FROM MAVENSMATE]: '+json.dumps(self.response, indent=4)
        self.__print_to_panel(msg)

    def __handle_generic_command_result(self):
        '''
            {'success': True, 'result': 'Started logging for debug users'}
        '''
        msg = ''
        if 'success' in self.response and self.response['success']:
            msg = 'Success'
            if 'result' in self.response:
                msg += ': '+self.response['result']
        elif 'success' in self.response and not self.response['success']:
            msg = '[OPERATION FAILED]'
            if 'error' in self.response:
                msg += ': '+self.response['error']
            elif 'result' in self.response:
                msg += ': '+self.response['result']
        self.__print_to_panel(msg)

    def __handle_delete_metadata_result(self, **kwargs):
        debug('HANDLING DELETE!')
        debug(self.response)
        self.__handle_compile_response()

    def __handle_compile_response(self, **kwargs):
        debug('HANDLING COMPILE!')
        debug(self.response)

        '''
            LIGHTNING:
            {
              "result": "markup:\/\/mm2:bar:3,19: ParseError at [row,col]:[4,19]\nMessage: XML document structures must start and end within the same entity.: Source",
              "success": false,
              "stack": "FIELD_INTEGRITY_EXCEPTION: markup:\/\/mm2:bar:3,19: ParseError at [row,col]:[4,19]\nMessage: XML document structures must start and end within the same entity.: Source\n    at onResponse (\/Users\/josephferraro\/Development\/Github\/MavensMate\/node_modules\/jsforce\/lib\/connection.js:368:13)\n    at _fulfilled (\/Users\/josephferraro\/Development\/Github\/MavensMate\/node_modules\/jsforce\/node_modules\/q\/q.js:798:54)\n    at self.promiseDispatch.done (\/Users\/josephferraro\/Development\/Github\/MavensMate\/node_modules\/jsforce\/node_modules\/q\/q.js:827:30)\n    at Promise.promise.promiseDispatch (\/Users\/josephferraro\/Development\/Github\/MavensMate\/node_modules\/jsforce\/node_modules\/q\/q.js:760:13)\n    at \/Users\/josephferraro\/Development\/Github\/MavensMate\/node_modules\/jsforce\/node_modules\/q\/q.js:574:44\n    at flush (\/Users\/josephferraro\/Development\/Github\/MavensMate\/node_modules\/jsforce\/node_modules\/q\/q.js:108:17)\n    at process._tickCallback (node.js:419:13)"
            }

            TOOLING/METADATA:
            {
              "result": {
                "checkOnly": false,
                "completedDate": "",
                "createdBy": "",
                "createdByName": "",
                "createdDate": "",
                "details": {
                  "componentSuccesses": [

                  ],
                  "runTestResult": {
                    "numFailures": "0",
                    "numTestsRun": "0",
                    "totalTime": "0.0"
                  },
                  "componentFailures": [
                    {
                      "attributes": {
                        "type": "ContainerAsyncRequest",
                        "url": "\/services\/data\/v32.0\/tooling\/sobjects\/ContainerAsyncRequest\/1dro0000000mhNbAAI"
                      },
                      "Id": "1dro0000000mhNbAAI",
                      "MetadataContainerId": "1dco0000000JuxBAAS",
                      "MetadataContainerMemberId": null,
                      "State": "Failed",
                      "IsCheckOnly": false,
                      "DeployDetails": {
                        "allComponentMessages": [
                          {
                            "changed": false,
                            "columnNumber": -1,
                            "componentType": "ApexClass",
                            "created": false,
                            "createdDate": "2015-02-12T02:59:21.986+0000",
                            "deleted": false,
                            "fileName": "ChangePasswordController",
                            "forPackageManifestFile": false,
                            "fullName": "ChangePasswordController",
                            "id": "01po0000001iVdVAAU",
                            "knownPackagingProblem": false,
                            "lineNumber": 16,
                            "problem": "expecting right curly bracket, found '&lt;EOF&gt;'",
                            "problemType": "Error",
                            "requiresProductionTestRun": false,
                            "success": false,
                            "warning": false
                          }
                        ],
                        "componentFailures": [
                          {
                            "changed": false,
                            "columnNumber": -1,
                            "componentType": "ApexClass",
                            "created": false,
                            "createdDate": "2015-02-12T02:59:21.986+0000",
                            "deleted": false,
                            "fileName": "ChangePasswordController",
                            "forPackageManifestFile": false,
                            "fullName": "ChangePasswordController",
                            "id": "01po0000001iVdVAAU",
                            "knownPackagingProblem": false,
                            "lineNumber": 16,
                            "problem": "expecting right curly bracket, found '&lt;EOF&gt;'",
                            "problemType": "Error",
                            "requiresProductionTestRun": false,
                            "success": false,
                            "warning": false
                          }
                        ],
                        "componentSuccesses": [

                        ],
                        "runTestResult": null
                      },
                      "ErrorMsg": null
                    }
                  ]
                },
                "done": false,
                "id": "",
                "ignoreWarnings": false,
                "lastModifiedDate": "",
                "numberComponentErrors": 1,
                "numberComponentsDeployed": 0,
                "numberComponentsTotal": 0,
                "numberTestErrors": 0,
                "numberTestsCompleted": 0,
                "numberTestsTotal": 0,
                "rollbackOnError": false,
                "runTestsEnabled": "false",
                "startDate": "",
                "status": "",
                "success": false
              }
            }
        '''

        #diffing with server
        if 'actions' in self.response and util.to_bool(self.response['success']) == False:
            diff_merge_settings = config.settings.get('mm_diff_server_conflicts', False)
            if diff_merge_settings:
                if sublime.ok_cancel_dialog(self.response["body"], self.response["actions"][0].title()):
                    self.__print_to_panel("Diffing with server")
                    th = MavensMateDiffThread(self.thread.window, self.thread.view, self.response['tmp_file_path'])
                    th.start()
                else:
                    self.__print_to_panel(self.response["actions"][1].title())
            else:
                if sublime.ok_cancel_dialog(self.response["body"], "Overwrite Server Copy"):
                    self.__print_to_panel("Overwriting server copy")
                    self.thread.params['action'] = 'overwrite'
                    if kwargs.get("callback", None) != None:
                        sublime.set_timeout(lambda: self.callback('compile', params=self.thread.params), 100)
                else:
                    self.__print_to_panel(self.response["actions"][1].title())
        else:
            try:
                success = self.response['result']['success']
                if success:
                    util.clear_marked_line_numbers(self.thread.view)
                    self.__print_to_panel("Success")
                    self.printer.hide()
                    return

                msg = '[OPERATION FAILED]: '

                if type(self.response['result']['details']['componentFailures']) is not list:
                    self.response['result']['details']['componentFailures'] = [self.response['result']['details']['componentFailures']]

                for res in self.response['result']['details']['componentFailures']:
                    if 'DeployDetails' in res:
                        for detail in res['DeployDetails']['componentFailures']:
                            debug(detail)
                            line_col = ''
                            line, col = 1, 1
                            if 'lineNumber' in detail:
                                line = int(detail['lineNumber'])
                                line_col = ' (Line: '+str(line)
                                util.mark_line_numbers(self.thread.view, [line], 'bookmark')
                            if 'columnNumber' in detail:
                                col = int(detail['columnNumber'])
                                line_col += ', Column: '+str(col)
                            if len(line_col):
                                line_col += ')'

                            #scroll to the line and column of the exception
                            if settings.get('mm_compile_scroll_to_error', True):
                                view = self.thread.view
                                pt = view.text_point(line-1, col-1)
                                view.sel().clear()
                                view.sel().add(sublime.Region(pt))
                                view.show(pt)

                            msg += detail['fileName']+': '+ detail['problem'] + line_col + '\n'
                    else: # metadata api?
                        msg += res['fullName']+': '+ res['problem'] + '\n'

                self.__print_to_panel(msg)

            except Exception as e:
                debug(e)
                debug(traceback.print_exc())
                debug(type(self.response))
                msg = ""
                if type(self.response) is dict:
                    if 'body' in self.response:
                        msg = self.response["body"]
                    else:
                        msg = json.dumps(self.response)
                elif type(self.response) is str:
                    try:
                        m = json.loads(self.response)
                        msg = m["body"]
                    except:
                        msg = self.response
                else:
                    msg = "Check Sublime Text console for error and report issue to MavensMate-SublimeText GitHub project."
                self.__print_to_panel('[OPERATION FAILED]: ' + msg)

    def __handle_coverage_result(self):
        if self.response == []:
            self.__print_to_panel("No coverage information for the requested Apex Class")
        elif 'records' in self.response and self.response["records"] == []:
            self.__print_to_panel("No coverage information for the requested Apex Class")
        else:
            if 'records' in self.response:
                self.response = self.response['records']
            if type(self.response) is list:
                record = self.response[0]
            else:
                record = self.response
            msg = str(record["percentCovered"]) + "%"
            util.mark_uncovered_lines(self.thread.view, record["Coverage"]["uncoveredLines"])
            self.__print_to_panel('[PERCENT COVERED]: ' + msg)

    def __handle_org_wide_coverage_result(self):
        if 'PercentCovered' not in self.response:
            self.__print_to_panel("No coverage information available")
        else:
            msg = str(self.response["PercentCovered"]) + "%"
            self.__print_to_panel('[ORG-WIDE TEST COVERAGE]: ' + msg)

    def __handle_coverage_report_result(self):
        if self.response == []:
            self.__print_to_panel("No coverage information available")
        elif 'records' in self.response and self.response["records"] == []:
            self.__print_to_panel("No coverage information available")
        else:
            if 'records' in self.response:
                self.response = self.response['records']
            apex_names = []
            new_dict = {}
            for record in self.response:
                apex_names.append(record["ApexClassOrTriggerName"])
                new_dict[record["ApexClassOrTriggerName"]] = record
            apex_names.sort()
            cls_msg = "Apex Classes:\n"
            trg_msg = "Apex Triggers:\n"
            for apex_name in apex_names:
                msg = ''
                record = new_dict[apex_name]
                coverage_key = ''
                if record["percentCovered"] == 0:
                    coverage_key = ' !!'
                elif record["percentCovered"] < 75:
                    coverage_key = ' !'
                if record["ApexClassOrTrigger"] == "ApexClass":
                    apex_name += '.cls'
                else:
                    apex_name += '.trigger'
                coverage_bar = '[{0}{1}] {2}%'.format('='*(round(record["percentCovered"]/10)), ' '*(10-(round(record["percentCovered"]/10))), record["percentCovered"])
                msg += '   - '+apex_name+ ':'
                msg += '\n'
                msg += '      - coverage: '+coverage_bar + "\t("+str(record["NumLinesCovered"])+"/"+str(record["NumLinesCovered"]+record["NumLinesUncovered"])+")"+coverage_key
                msg += '\n'
                if record["ApexClassOrTrigger"] == "ApexClass":
                    cls_msg += msg
                else:
                    trg_msg += msg
            self.__print_to_panel('Success')
            new_view = self.thread.window.new_file()
            new_view.set_scratch(True)
            new_view.set_name("Apex Code Coverage")
            if "linux" in sys.platform or "darwin" in sys.platform:
                new_view.set_syntax_file(os.path.join("Packages","YAML","YAML.tmLanguage"))
            else:
                new_view.set_syntax_file(os.path.join("Packages/YAML/YAML.tmLanguage"))
            sublime.set_timeout(new_view.run_command('generic_text', {'text': cls_msg+trg_msg }), 1)

    def __handle_apex_script_result(self):
        '''
            {
              "result": {
                "\/Users\/josephferraro\/Desktop\/dfs\/apex-scripts\/coolscript.cls": {
                  "line": -1,
                  "column": -1,
                  "compiled": true,
                  "success": true,
                  "compileProblem": null,
                  "exceptionStackTrace": null,
                  "exceptionMessage": null
                }
              },
              "success": true
            }
        '''
        debug(self.result)
        res = self.result[ self.thread.flags[0] ]
        debug(res)
        if res['success'] and res['compiled']:
            self.__print_to_panel("Success")
        elif not res['success']:
            message = "[OPERATION FAILED]: "
            if "compileProblem" in res and res["compileProblem"] != None:
                message += "[Line: "+str(res["line"]) + ", Column: "+str(res["column"])+"] " + res["compileProblem"] + "\n"
            if "exceptionMessage" in res and res["exceptionMessage"] != None:
                message += res["exceptionMessage"] + "\n"
            if "exceptionStackTrace" in res and res["exceptionStackTrace"] != None:
                message += res["exceptionStackTrace"] + "\n"
            self.__print_to_panel(message)

    def __handle_test_result(self):
        '''
            {
              "result": {
                "testResults": {
                  "ChangePasswordControllerTest": {
                    "attributes": {
                      "type": "ApexTestQueueItem",
                      "url": "\/services\/data\/v32.0\/tooling\/sobjects\/ApexTestQueueItem\/709o0000000DUTXAA4"
                    },
                    "ApexClassId": "01po0000001iVdWAAU",
                    "ApexClass": {
                      "attributes": {
                        "type": "ApexClass",
                        "url": "\/services\/data\/v32.0\/tooling\/sobjects\/ApexClass\/01po0000001iVdWAAU"
                      },
                      "Name": "ChangePasswordControllerTest"
                    },
                    "Status": "Completed",
                    "ExtendedStatus": "(0\/1)",
                    "results": [
                      {
                        "attributes": {
                          "type": "ApexTestResult",
                          "url": "\/services\/data\/v32.0\/tooling\/sobjects\/ApexTestResult\/07Mo0000002IOAdEAO"
                        },
                        "Outcome": "Fail",
                        "ApexClassId": "01po0000001iVdWAAU",
                        "ApexClass": {
                          "attributes": {
                            "type": "ApexClass",
                            "url": "\/services\/data\/v32.0\/tooling\/sobjects\/ApexClass\/01po0000001iVdWAAU"
                          },
                          "Name": "ChangePasswordControllerTest"
                        },
                        "MethodName": "testChangePasswordController",
                        "Message": "System.AssertException: Assertion Failed",
                        "StackTrace": "Class.mm2.ChangePasswordControllerTest.testChangePasswordController: line 13, column 1",
                        "ApexLogId": "07Lo000000SpsbJEAR"
                      }
                    ]
                  }
                },
                "coverageResults": {
                  "classes": {
                    "ChangePasswordController": {
                      "coveredLines": [
                        5,
                        6,
                        7,
                        9,
                        10,
                        11,
                        14
                      ],
                      "uncoveredLines": [

                      ],
                      "totalLines": 7,
                      "percentCovered": 100
                    }
                  },
                  "triggers": {

                  }
                }
              },
              "success": true
            }
        '''
        msg = ''

        debug(self.response['result']['testResults'])

        for test_class_name in self.response['result']['testResults'].keys():

            debug(test_class_name)
            debug(self.response['result']['testResults'][test_class_name])

            test_result = self.response['result']['testResults'][test_class_name]
            tests_passed_vs_failed = test_result['ExtendedStatus']

            tests_passed_vs_failed = tests_passed_vs_failed.replace('(', '').replace(')','')
            if tests_passed_vs_failed.split('/')[0] != tests_passed_vs_failed.split('/')[1]:
                msg += '[TEST RESULT]: FAIL'
            else:
                msg += '[TEST RESULT]: PASS'

            msg += '\n\n' + test_class_name + ': ' + test_result['ExtendedStatus'] + ' Passed'

            for r in test_result['results']:
                msg += '\n\n METHOD RESULT \n'
                msg += "{0} : {1}".format(r['MethodName'], r['Outcome'])

                if "StackTrace" in r and r["StackTrace"] != None:
                    msg += "\n\n"
                    msg += " STACK TRACE "
                    msg += "\n"
                    msg += r["StackTrace"]

                if "Message" in r and r["Message"] != None:
                    msg += "\n\n"
                    msg += " MESSAGE "
                    msg += "\n"
                    msg += r["Message"]
                    msg += "\n"

            # if len(self.response) == 1:
            #     res = self.response[0]
            #     response_string = ""
            #     if 'detailed_results' in res:
            #         all_tests_passed = True
            #         for r in res['detailed_results']:
            #             if r["Outcome"] != "Pass":
            #                 all_tests_passed = False
            #                 break

            #         if all_tests_passed:
            #             response_string += '[TEST RESULT]: PASS'
            #         else:
            #             response_string += '[TEST RESULT]: FAIL'

            #         for r in res['detailed_results']:
            #             if r["Outcome"] == "Pass":
            #                 pass #dont need to write anything here...
            #             else:
            #                 response_string += '\n\n'
            #                 rstring = " METHOD RESULT "
            #                 rstring += "\n"
            #                 rstring += "{0} : {1}".format(r["MethodName"], r["Outcome"])

            #                 if "StackTrace" in r and r["StackTrace"] != None:
            #                     rstring += "\n\n"
            #                     rstring += " STACK TRACE "
            #                     rstring += "\n"
            #                     rstring += r["StackTrace"]

            #                 if "Message" in r and r["Message"] != None:
            #                     rstring += "\n\n"
            #                     rstring += " MESSAGE "
            #                     rstring += "\n"
            #                     rstring += r["Message"]
            #                     rstring += "\n"
            #                 #responses.append("{0} | {1} | {2} | {3}\n".format(r["MethodName"], r["Outcome"], r["StackTrace"], r["Message"]))
            #                 responses.append(rstring)
            #         response_string += "\n\n".join(responses)
            #         self.__print_to_panel(response_string)
            #         self.printer.scroll_to_bottom()
            #     else:
            #         self.__print_to_panel(json.dumps(self.response))
            # elif len(self.response) > 1:
            #     #run multiple tests
            #     response_string = ''
            #     for res in self.response:
            #         if 'detailed_results' in res:
            #             all_tests_passed = True
            #             for r in res['detailed_results']:
            #                 if r["Outcome"] != "Pass":
            #                     all_tests_passed = False
            #                     break

            #             if all_tests_passed:
            #                 response_string += res['ApexClass']['Name']+':\n\tTEST RESULT: PASS'
            #             else:
            #                 response_string += res['ApexClass']['Name']+':\n\tTEST RESULT: FAIL'

            #             for r in res['detailed_results']:
            #                 if r["Outcome"] == "Pass":
            #                     pass #dont need to write anything here...
            #                 else:
            #                     response_string += '\n\n'
            #                     response_string += "\t METHOD RESULT "
            #                     response_string += "\t\n"
            #                     response_string += "\t{0} : {1}".format(r["MethodName"], r["Outcome"])

            #                     if "StackTrace" in r and r["StackTrace"] != None:
            #                         response_string += "\n\n"
            #                         response_string += "\t STACK TRACE "
            #                         response_string += "\t\n"
            #                         response_string += "\t"+r["StackTrace"].replace("\n","\t\n")

            #                     if "Message" in r and r["Message"] != None:
            #                         response_string += "\n\n"
            #                         response_string += "\t MESSAGE "
            #                         response_string += "\t\n"
            #                         response_string += "\t"+r["Message"].replace("\n","\t\n")
            #                         response_string += "\n"
            #         response_string += "\n\n"
            #     #self.__print_to_panel(response_string)
            #     #self.printer.scroll_to_bottom()

            #     self.__print_to_panel('Success')
            #     new_view = self.thread.window.new_file()
            #     new_view.set_scratch(True)
            #     new_view.set_name("Run All Tests Result")
            #     if "linux" in sys.platform or "darwin" in sys.platform:
            #         new_view.set_syntax_file(os.path.join("Packages","YAML","YAML.tmLanguage"))
            #         new_view.set_syntax_file(os.path.join("Packages","MavensMate","sublime","panel","MavensMate.hidden-tmLanguage"))
            #     else:
            #         new_view.set_syntax_file(os.path.join("Packages/MavensMate/sublime/panel/MavensMate.hidden-tmLanguage"))

            #     sublime.set_timeout(new_view.run_command('generic_text', {'text': response_string }), 1)

        self.__print_to_panel(msg)
