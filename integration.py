#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ver 2.20.0723

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
dirname, filename = os.path.split(os.path.abspath(__file__))
print ('parent dir: {}     current dir: {}'.format(parentdir, currentdir))
sys.path.insert(0,parentdir)
# sys.path.insert(0,parentdir+"/lib")

import time, sys, inspect, os
import random as rd
from pathlib import Path
from enum import Enum
from datetime import datetime
import json

import logging
from logging.handlers import RotatingFileHandler

from api.echoes_hardware_api import *
from api.echoes_signal_processing_api import *
from api.echoes_utils_api import *
# from api.echoes_models_api import *

from api.scorpion_hardware import *
from api.scorpion_echoes import *
from api.echoes_database_api import *

# from Titan2lCtrl.Scorpion import *
# from Titan2lCtrl.Enclosure import *
# from Titan2lCtrl.api.echoes_utils_api import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler
# handler = logging.FileHandler('./Exchange/logs/auto-test.log')
print ('parent dir: {}     current dir: {}'.format(parentdir, currentdir))
handler = RotatingFileHandler(parentdir + '/Titan2l/Exchange/logs/GUI.log', maxBytes=500000,
                                  backupCount=50)
# create a loggign format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s')
handler.setFormatter(formatter)

# add the file handler to the logger
logger.addHandler(handler)
logger.info("\n --------------- Start logging ----------------- ")
log_data = {
    'total' : 0,
    'lower_arm': 0,
    'temp' : 0,
    'raise_arm' : 0,
    'capture' : 0,
    'push_button':0
}
logger.info("Reset captureID: {}".format(log_data))


logger = logging.getLogger("Rotating Log")
logger.setLevel(logging.DEBUG)

logger.addHandler(handler)

echoes_2    = scorpion_echoes(debug=True, debug_level=2)
Enclosure   = Scorpion_hw(debug=True, debug_level=2)


def main():
    logger.info("Open GUI")
    run_GUI()
    
    ''' For waiting screen '''
    animation = "|/-\\"
    idx = 0


    request_path = Path(echoes_2.GUI_home_folder + '/Titan2l/Exchange/request.json')
    result_path = Path(echoes_2.GUI_home_folder + '/Titan2l/Exchange/result.json')

    print('[state] Enter test loop')
    print('path to check {}'.format(request_path))
    while (1):
        # echoes_2.clear_result()     # BUG: testID cannot increment if cleared
        
        if request_path.exists():
            #''' WARNING: Enable this to activate timeout=15s
            #Otherwise, constantly waiting for push button. 
            #Web-app scropion cannot use while waiting for button
            # os.remove(request_path)
            # logger.info("removed request json file")
            #'''
            
            echoes_2.clear_result()     # BUG: testID cannot increment if cleared
            logger.info("remove previouses result")
            
            buttonPushed = True
            buttonPushed = Enclosure.pushButton()
            logger.info("activate button")
            
            
            try:
                buttonPushed = Enclosure.pushButton()
                logger.info("activate button")
            
            except RuntimeError as e:
                logger.warning('push button runtime {}\n'.format(e))
                log_data['push_button'] += 1
                print ("WARNING: pushbutton runtime error")
                pass
            except Exception as e:
                logger.error('Push Button error: {}\n'.format(e))
                log_data['push_button'] += 1
                pass
            

            if buttonPushed:
                time.sleep(0.1)
                logger.info("button held 3s")
                
                try:
                    logger.info('Lower Arm')
                    loweringServo = Enclosure.lowerArm()
                except OSError:
                    # continue
                    print ("reset arduino")
                    Enclosure.resetArduino()
                except RuntimeError as e:
                    logger.warning('Lower_arm {}\n'.format(e))
                    log_data['lower_arm'] += 1
                    time.sleep(2.5)
                    print ("lower mode run too fast")
                except Exception as e:
                    logger.error('Lower_arm: {}\n'.format(e))
                    log_data['lower_arm'] += 1
                    pass
                
                time.sleep(1.5)
                logger.info("Capture signal and DSP")
                TEST_SCAN()

                
                try:
                    time.sleep(0.1)
                    logger.info('Raise Arm')
                    raisingTail = Enclosure.raiseArm()
                except OSError:
                    # continue
                    print ("reset arduino")
                    Enclosure.resetArduino()
                except RuntimeError as e:
                    logger.warning('Raise_arm {}\n'.format(e))
                    log_data['raise_arm'] += 1
                    time.sleep(2.5)
                    print ("raise mode run too fast")
                except Exception as e:
                    logger.error('Raise_arm: {}\n'.format(e))
                    log_data['raise_arm'] += 1
                    pass
                
                os.remove(request_path)
                logger.info("removed request json file")
                
                log_data['total'] += 1
                logger.info('Stats {}\n\n'.format(log_data))
                
                print ('test completed\n')
                time.sleep(3)
            
            else:
                logger.debug("Timeout. No button held")
                print('test Timeout \n')

                ''' Save a dummy value to file and display TEST FAILED '''
                # echoes_2.save_scan_result(soh=-1, soc=-1, battTemp=-1, ambientTemp=-1)


        else:
            ''' time delay for polling next request '''
            print("waiting USER request  " + animation[idx % len(animation)], end="\r")
            idx += 1
            time.sleep(0.1)

    return

def run_GUI():
    # Popen('screen -dm -S gui mono /home/pi/Titan2l/Titan2lGui/Titan2l.exe')
    #Popen('screen -dm -S gui mono ' + echoes_2.GUI_home_folder + '/Titan2l/Titan2lGui/Titan2l.exe')
    print('successfully run the GUI in another screen session')

def TEST_SCAN():
    echoes_signal, echoes_signal_filtered = {}, {}
    battTemp, ambientTemp = -1, -1
    soh, soc = None, -1

    echoes_session_config = {
        # 'input_adc' : 'adc-secondary',
        'transmitter_channel' : 'a-tx',
        'receiver_channel' : 'c-rx',
        'input_impulse_type' : 'bipolar',
        'impulse_width' : 370,
        'vga_gain' : 0.25,
        'total_captures' : 16,
        'delay_interval':  1,
        'input_gen_impulse' : 'gen_impulse',
    }

    logger.debug('Acquire signal in dual channel')
    for sig_num in range(2):
        ''' ---------- Run a Capture ------------'''
        adc_captures_float, adc_captures_filtered, _ = echoes_2.capture_and_read_adc(
                                            remove_bad_reads=False, bandpass=True)
        signal_name = f"{echoes_session_config['transmitter_channel']}"\
                    f"-{echoes_session_config['receiver_channel']}"
        echoes_signal[signal_name] = [i for i in adc_captures_float]
        echoes_signal_filtered[f"{signal_name}_filtered"] = [j for j in adc_captures_filtered]
        
        if echoes_session_config['transmitter_channel'] == 'a-tx':
            echoes_session_config['transmitter_channel'] = 'b-tx'
        elif echoes_session_config['transmitter_channel'] == 'b-tx':
            echoes_session_config['transmitter_channel'] = 'a-tx'
        elif echoes_session_config['transmitter_channel'] == 'c-tx':
            echoes_session_config['transmitter_channel'] = 'd-tx'
        elif echoes_session_config['transmitter_channel'] == 'd-tx':
            echoes_session_config['transmitter_channel'] = 'c-tx'
        
        if echoes_session_config['receiver_channel'] == 'a-rx':
            echoes_session_config['receiver_channel'] = 'b-rx'
        elif echoes_session_config['receiver_channel'] == 'b-rx':
            echoes_session_config['receiver_channel'] = 'a-rx'
        elif echoes_session_config['receiver_channel'] == 'c-rx':
            echoes_session_config['receiver_channel'] = 'd-rx'
        elif echoes_session_config['receiver_channel'] == 'd-rx':
            echoes_session_config['receiver_channel'] = 'c-rx'
        time.sleep(0.05)

        try:
            logger.debug('Read TempC')
            battTemp, ambientTemp = Enclosure.readTempC()
        except RuntimeError as e:
            logger.warning(f"Temp Read out {e}")
            log_data['temp'] += 1
            battTemp, ambientTemp = -1, -1
        except Exception as e:
            logger.error(f"Temp Read out: {e}")
            log_data['temp'] += 1
            battTemp, ambientTemp = -1, -1
            pass
        
        time.sleep(1)

    logger.debug('Run the model')
    # soh = nn_model_predict(echoes_signal)
    soh, soc = -1.0, -1.0
    print (f"\t\tsoh:{soh}  soc:{soc}")

    logger.debug('Save save_scan_result')
    scorpion_data = echoes_2.save_scan_result(soh, soc, battTemp, ambientTemp)
    print (scorpion_data)

    time_taken = datetime.datetime.utcnow().isoformat()
    batteryModel = "APPL"
    gen = "06"
    form = "C"
    Battery = {
        "batteryUid": f"{batteryModel}",
        "manufacturerSuppliedUid": None,  # QR code
        "batteryModel" : batteryModel,
        "batteryGeneration": gen,
        "batteryVariant": "0",
        "formFactor": form,
        "batteryType": "ip62014-2018-APL-C-2.915Plus-6"
    }

    Device = {
        "testDeviceId" : "S-204",
        "echoesId" :"0x042E6236",
        "firmwareVersion": "2.5",
        "commissionTime" : "",
        "deviceCharacteristics" : "",
    }

    TestEvent = {
        "eventId" : "",
        "batteryUId" : Battery["batteryUid"],
        "timestamp" : time_taken,
        "testDeviceId" : Device["testDeviceId"],
        "echoesId" : "0x042E6236",
        "projectName" : "Apple-Schneider-project"
    }

    ExperimentParameters = {
        "testDeviceId" : Device["testDeviceId"],
        "batteryUId" : Battery["batteryUid"],
        "echoesId": "0x042E6236",
        "intervalBetweenSamples": 1,
        "numberOfSamples": 64,
        "impulseVoltage": 90.0,
        "impulseWidth": 600,
        "impulseType": "bipolar-negative",
        # "inputChannel": "adc-ch-b",
        "vgaGain": 0.55,
        "inputAdc": ['a-tx-c-rx'],
        "samplingFrequency": 7200000.0,
        "temperatureSensorId": "MLX90632",
        "temperatureObject": 0.0,
        "temperatureAmbient": None,
    }

    SignalRaw = {
        "experimentId": None,
        "eventId": TestEvent['eventId'],
        "echoesOutput": echoes_signal,  # 64 raw signals
    }

    SignalProcessed = {
        "eventId": TestEvent['eventId'],
        "echoesOutputProcessed": {},
        "predictedSoC": -1.0,
        "predictedSoH": -1.0,
        "modelUsed": None
    }

    data_to_webportal = {
        "Battery" : Battery,
        "TestEvent" : TestEvent,
        "SignalProcessed" : SignalProcessed
    }

    # res_portal = process_echoes_data(data_to_webportal)
    
    res_validate = validate(data_to_webportal)
    if res_validate["status"] == "success" and res_validate["validation"] == 1:
        res_predict = predict(data_to_webportal)

        if res_predict["status"] == "success":
            
    with open(Path('/home/pi/echoes-two-host-app/host-app/Titan2l/data/sample_file.json'), 'w') as writeout:
        json.dump(data_to_webportal, writeout, sort_keys=False, 
            indent=2, separators=(',', ': '))
        # writeout.write(json.dumps(scan_data))
    writeout.close()

    print (res_portal)

    data_to_webportal.clear()

    # logger.debug('Generate QR code')
    # Scorpion.qr_generator()
    

if __name__ == '__main__':
    main()
