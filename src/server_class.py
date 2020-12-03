"""
This file contains the main code.


This class was coded as part of a distributed computing tutorial.
The main idea behind this code is  demonstrate the use of Pyro4.



"""


import Pyro4
from aniachi.systemUtils import Welcome as W
import psutil
from cowpy import cow
from io import StringIO, BytesIO
import requests
from PIL import Image
from PIL import ImageFont, ImageDraw
from datetime import datetime
import logging
import os
import sys
import numpy as np
import unittest
import platform
from aniachi.timeUtils import elapsedtime as Et
import subprocess
import sys


log_file = 'pyro4log.log'
'''The log will be written into that  file name '''

log_path = '/tmp/distribuited'
'''The full path to the log file. This path must be mounted on a shared volume between the docker container and the host's file system'''

_background_image = 'common.png'
'''This image is going to be used as a watermark in the upper right side of the processed image by your server class.'''

_FONT_NAME_MAC = 'Helvetica.ttc'
'''The name of the file that contains the font. This file must be unloaded when creating the docker container. The Font will be used to write on the processed image. '''

_FONT_NAME_LINUX = '/root/pyro4/python_distributed/fonts/font-reg.ttf'

_output_file_name = 'output_file.png'
'''If we are debugging the application (debug=True ). The image will be saved in the local file system using the given name to this variable'''

_debug = True
'''Debug flag '''

PORT = 9000
'''Server port'''


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Server(object):
    '''
    Main Object

    Args:
        object ([type]): Extends from object 
    '''

    def __init__(self):
        """Object Constructor

        basically, our  constructor does
        create a log file
        Build the watermark object
        load the fonts from a specific path 
        If something goes terrible wrong then the object exits the program sending syserrr message -1 back to the os



        """
        print('BUILD OBJECT FROM REMOTE IP '+str(Pyro4.current_context.client.sock.getpeername()
                                                 [0]) if Pyro4.current_context.client is not None else 'LOCAL BUILD')

        current_path = os.path.join(log_path, log_file)
        print('Logger  file @ ', current_path)
        try:
            if not os.path.exists(log_path):
                os.makedirs(log_path)
        except Exception as e:
            print(e)
            sys.exit(-1)
        logging.basicConfig(filename=current_path, format='%(asctime)s %(levelname)-8s -- %(message)s --',
                            level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('INIT MAIN OBJECT')
        logging.info('BUILD OBJECT FOR REMOTE IP '+str(Pyro4.current_context.client.sock.getpeername()
                                                       [0]) if Pyro4.current_context.client is not None else 'LOCAL BUILD')
        try:
            self.watermark = Image.open(_background_image).resize((200, 250))
            '''WATERMARK PICTURE  TO BE USED AS BAXKGROUND'''
            logging.info(
                "READING BACKGROUD IMAGE {0}".format(_background_image))
        except Exception as e:
            logging.critical(
                "SERVER CAN'T READ BACKGROUD IMAGE {0}".format(_background_image))
            print("SERVER CANOT READ BACKGROUD IMAGE {0} ... EXIT".format(
                _background_image))
            sys.exit(-1)
        try:
            if sys.platform == 'linux':
                self.font = ImageFont.truetype(_FONT_NAME_LINUX, 28)
                logging.info("READING FONT FILE {0}".format(_FONT_NAME_LINUX))
            elif sys.platform == 'darwin':
                self.font = ImageFont.truetype(_FONT_NAME_MAC, 28)
                logging.info("READING FONT FILE {0}".format(_FONT_NAME_MAC))
            else:
                logging.critical(
                    "SERVER CAN'T READ FONT FILE. OS DETECTED {0}".format(sys.platform))
                print("SERVER CAN'T READ FONT FILE.\nOS DETECTED {0} EXIT.....".format(
                    sys.platform))
                sys.exit(-1)

        except Exception as e:
            logging.critical(
                " SERVER CAN'T READ FONT FILE  ... EXIT")
            print(
                "SERVER CAN'T READ FONT FILE   ... EXIT")
            sys.exit(-1)

    @staticmethod
    def validate_rbga(t):
        '''

        :param t:
        :return:
        '''

        if type(t) is tuple and len(t) == 4 and all(type(octet) is int for octet in t) and all(
                0 <= octet <= 255 for octet in t):
            pass
        else:
            raise ValueError(
                'Color must be a tuple of 4 octets like (14,32,41,12)')

    def get_server_info(self, format='json'):
        '''
        Get all available server information
        like python version or OS name etc

        :param format: format as Str or as dict
        :return: Return all avaiblable Information as String or as dictionay
        :rtype: str, dict
        '''

        logging.info('CALLING get_server_info() FROM  REMOTE IP ' + str(Pyro4.current_context.client.sock.getpeername()[
            0]) if Pyro4.current_context.client is not None else 'LOCAL CALL')

        return W.get_fetchdata(format=format)

    def get_cpu_snapshot(self, format=str):
        '''


        :param format:
        :return: Returns the percentage of use of each core as a dictionary. Where each key is the core and the value is the percentage of use. The Value could be expressed as a float or as a String. Example {'Core 1': 11.2} or {'Core 1': "11.2 %"}
        :rtype: dict
        '''
        logging.info('CALLING get_cpu_snapshot() FROM  REMOTE IP ' + str(Pyro4.current_context.client.sock.getpeername()[
            0]) if Pyro4.current_context.client is not None else 'LOCAL CALL')
        d = dict()
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            d['core '+str(i)] = f'{percentage} %'.format(
                percentage) if format == str else percentage
        return d

    def __get_str_to_log(self, params, f_name):
        '''

        '''
        del (params['self'])
        s = StringIO()
        s.write(f_name)
        s.write('(')
        for t in params.keys():
            s.write(t)
            s.write(':')
            s.write(str(params[t]))
            s.write(', ')

        s.write(')')
        return s.getvalue()

    def get_cow_cpu(self):
        '''
        :return:
        '''
        logging.info(
            'CALLING get_cow_cpu() FROM  REMOTE IP ' + str(Pyro4.current_context.client.sock.getpeername()[
                0]) if Pyro4.current_context.client is not None else 'LOCAL CALL')
        d = self.get_cpu_snapshot(format=None)
        keys = d.keys()
        s = StringIO()
        [s.write(k+':  '+str(d[k])+'\n') for k in keys]
        return self.get_funny_text(s.getvalue())

    def get_funny_text(self, t="sample"):
        '''
        This method just print the famous cow
         ________
        < sample >
        --------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
              ||--WWW |
                ||     ||


        :param t: t
        :return: The ascii cow
        '''

        logging.info('CALLING get_funny_text() FROM  REMOTE IP ' + str(Pyro4.current_context.client.sock.getpeername()[
            0]) if Pyro4.current_context.client is not None else 'LOCAL CALL')
        if type(t) is not str:
            raise ValueError('expected string got {0}'.format(type(t)))
        cheese = cow.www()
        msg = cheese.milk(t)
        return msg

    def process_image(self, url='https://github.com/bygregonline/itunestomosaic/raw/master/orginal.jpg',  greyscale=False, color=(245, 0, 0, 225), img_format='PNG'):
        '''

        :param url:
        :param format:
        :param greyscale:
        :param color:
        :param img_format:
        :return:
        '''

        logging.info(
            'CALLING '+self.__get_str_to_log(locals(), 'process_image')+' FROM  REMOTE IP ' + str(Pyro4.current_context.client.sock.getpeername()[
                0]) if Pyro4.current_context.client is not None else 'LOCAL CALL')

        try:

            d = dict()
            d['ERROR'] = None

            try:
                Server.validate_rbga(color)
            except Exception as e:
                d['ERROR'] = 'INVALID COLOR FORMAT'
                d['STATUS'] = 'INVALID COLOR FORMAT {0} INSTEAD OF {1}'.format(
                    e, color)
                logging.error(
                    'INVALID COLOR FORMAT {0} INSTEAD OF {1}'.format(e, color))

                return d

            if type(greyscale) is not bool:
                d['ERROR'] = 'INVALID GREYSCALE'
                d['STATUS'] = 'GREYSCALE MUST BE True or False INSTEAD OF {0}'.format(
                    greyscale)
                logging.error(
                    'GREYSCALE MUST BE True or False INSTEAD OF {0}'.format(greyscale))
                return d
            if not (type(img_format) is str and img_format.upper() in ['JPG', 'PNG']):
                d['ERROR'] = 'INVALID IMG_FORMAT'
                d['STATUS'] = 'IMG_FORMAT MUST BE JPG or PNG INSTEAD OF {0}'.format(
                    img_format)
                logging.error(
                    'IMG_FORMAT MUST BE JPG or PNG INSTEAD OF {0}'.format(img_format))
                return d

            try:
                response = requests.get(url, allow_redirects=True)
                logging.info('downloading ... file {0}'.format(url))

                if response.status_code != 200:
                    d['ERROR'] = 'INTERNET ERROR'
                    d['STATUS'] = response.status_code
                    logging.error('INTERNET ERROR {0}'.format(
                        response.status_code))
                    return d
            except Exception as e:
                logging.exception('INTERNET ERROR {0}'.format(e))
                d['ERROR'] = 'INTERNET ERROR'
                d['STATUS'] = str(e)
                return d

            img = Image.open(BytesIO(response.content)).convert('RGBA')
            if greyscale:
                img = img.convert('L').convert('RGBA')

            img.paste(self.watermark, (0, 0), mask=self.watermark)
            txt = Image.new('RGBA', img.size, (255, 255, 255, 0))
            txt_draw = ImageDraw.Draw(txt)
            w, h = img.size
            msg = " © COPYRIGHT " + datetime.now().strftime("%b %d %Y %H:%M:%S")
            text_w, text_h = txt_draw.textsize(msg, self.font)
            pos = w - text_w - 10, (h - text_h) - 10
            txt_draw.text(pos, msg, font=self.font, fill=color, align="lett")

            out = Image.alpha_composite(img, txt)

            d['STATUS'] = 'OK'
            d['COLOR'] = color
            d['FORMAT'] = str(format)
            d['URL'] = url
            buffer = BytesIO()
            out.save(buffer, format=img_format)

            d['RAW'] = buffer.getvalue()

            try:
                if _debug:
                    out.save(_output_file_name)
            except Exception as e:
                logging.error('COULD NOT SAVE {0}'.format(_output_file_name))

            return d

        except Exception as e:
            logging.exception('UNHANDLED EXCEPTION')
            print('ERORR->', e)

    def matmul(self, seed=23):
        '''
        TDIO

        :return:
        '''
        d = dict()
        et = Et()
        if type(seed) is not int:
            raise ValueError(
                'According to the rule "safe", seed must be an integer')
        np.random.seed(seed)

        a = np.random.rand(12000, 1000)
        b = np.random.rand(1000, 10000)
        c = np.dot(a, b)
        d['SHAPE'] = c.shape
        d['SOMMATOIRE'] = np.sum(c)
        d['ELAPSED'] = et.getElapsedTime()

        return d

    def get_neofetch(self):
        '''

        :return: str
        '''
        result = subprocess.run(['neofetch'], stdout=subprocess.PIPE)
        return result.stdout.decode('utf-8')

    def __str__(self):
        '''
        Overrides __str__ method
        :return: str
        '''
        return "Development server  0.01"


class TestStringMethods(unittest.TestCase):
    '''
    All test cases extends from unittest.TestCase



    '''

    def setUp(self):
        '''
        This method builds the object that runs in all test cases possible scenarios
        The self.server variable should be used in all tests

        to run use this command

        python3 -m unittest server_class.py

        :return: None
        '''

        self.server = Server()
        '''The server variable should be called instead of building the object inside the test methods '''
        self.version = platform.python_version()
        '''The python version  is going to be used to validate the get_fetchdata() method '''



    def test_1(self):
        '''
        Runs all test for the method get_funny_text()

        :return: None
        '''
        print('Running test for  get_funny_text')
        self.assertEqual(type(self.server.get_funny_text()), str)
        self.assertRaises(ValueError, self.server.get_funny_text, None)
        self.assertRaises(ValueError, self.server.get_funny_text, {})
        self.assertRaises(ValueError, self.server.get_funny_text, [])
    #

    #
    def test_2(self):
        '''
        Runs all test for the method get_cow_cpu()

        :return: None
        '''
        print('Running test for  get_cow_cpu')
        self.assertEqual(type(self.server.get_cow_cpu()), str)
        self.assertRaises(TypeError, self.server.get_cow_cpu, None)
        self.assertRaises(TypeError, self.server.get_cow_cpu, 'None')
    #

    #
    def test_3(self):
        '''
        Runs all test for the method get_cpu_snapshot()

        :return: None
        '''
        print('Running test for  get_cpu_snapshot')

        self.assertRaises(TypeError, self.server.get_cpu_snapshot, l='None')
        self.assertEqual(type(self.server.get_cpu_snapshot()), dict)
        self.assertEqual(list(self.server.get_cpu_snapshot())[0][0:4], 'core')
        self.assertEqual(
            type(list(self.server.get_cpu_snapshot(format=None).values())[0]), float)
    #

    #
    def test_4(self):
        '''
        Runs all test for the static method validate_rbga()

        :return: None
        '''
        print('Running test for  validate_rbga')
        self.assertRaises(TypeError, Server.validate_rbga)
        self.assertRaises(ValueError, Server.validate_rbga, None)
        self.assertRaises(ValueError, Server.validate_rbga, (None, 7, 5, -1))
        self.assertRaises(ValueError, Server.validate_rbga, '(None, 7, 5, -)')
        self.assertRaises(ValueError, Server.validate_rbga, {})
        self.assertRaises(ValueError, Server.validate_rbga, (-1, 2, 1, 1))
        self.assertRaises(ValueError, Server.validate_rbga, (-0, 2, 256, 1))
        self.assertEqual(Server.validate_rbga((233, 233, 1, 1)), None)

    #

    #

    def test_5(self):
        '''
        Runs all test for the method get_server_info()

        :return: None
        '''
        print('Running test for  get_server_info')
        self.assertIs(type(self.server.get_server_info(format=dict)), dict)
        self.assertIs(type(self.server.get_server_info()), str)
        self.assertIs(type(self.server.get_server_info(
            format=dict)['Python Version']), str)
        self.assertEqual(self.server.get_server_info(
            format=dict)['Python Version'], self.version)
        self.assertNotEqual(type(self.server.get_server_info(None)), str)

    #

    #

    def test_6(self):
        '''
        Runs all test for the method process_image()

        :return: None
        '''

        print('Running test for  process_image')
        self.assertRaises(TypeError, self.server.process_image, greyscaeele='greyscale')
        self.assertEqual(self.server.process_image( img_format=None)['ERROR'], 'INVALID IMG_FORMAT')
        self.assertEqual(self.server.process_image(img_format='GIF')['ERROR'], 'INVALID IMG_FORMAT')
        self.assertEqual(self.server.process_image( greyscale='GIF')['ERROR'], 'INVALID GREYSCALE')
        self.assertEqual(self.server.process_image( greyscale=None)['ERROR'], 'INVALID GREYSCALE')
        self.assertEqual(self.server.process_image(greyscale=None)['ERROR'], 'INVALID GREYSCALE')
        self.assertEqual(self.server.process_image(color=[])['ERROR'], 'INVALID COLOR FORMAT')
        self.assertEqual(self.server.process_image(color=())['ERROR'], 'INVALID COLOR FORMAT')
        self.assertEqual(self.server.process_image(color=((None, 7, 5, -1)))['ERROR'], 'INVALID COLOR FORMAT')
        self.assertEqual(self.server.process_image(color=((0, 267, 5, 1)))['ERROR'], 'INVALID COLOR FORMAT')
        self.assertEqual(self.server.process_image( url='')['ERROR'], 'INTERNET ERROR')
        self.assertEqual(self.server.process_image( url='https://github.com/bygregonline/itunestomosaic/raw/master/orginal.jp')['ERROR'], 'INTERNET ERROR')
        self.assertEqual(self.server.process_image( url='https://github.com/bygregonline/itunestomosaic/raw/master/orginal.jp')['STATUS'], 404)
        self.assertEqual(type(self.server.process_image(None)), dict)
        aux = self.server.process_image()
        self.assertEqual(aux['STATUS'], 'OK')
        self.assertEqual(aux['ERROR'], None)
        self.assertEqual(type(aux), dict)
        self.assertEqual(type(aux['RAW']), bytes)


    def test_7(self):
        '''
        Runs all test against matmul() method

        :return:  None
        '''
        self.assertRaises(TypeError, self.server.matmul,
                          greyscaeele='greyscale')
        self.assertRaises(ValueError, self.server.matmul, seed=0.900)
        self.assertRaises(ValueError, self.server.matmul, seed=None)
        self.assertRaises(ValueError, self.server.matmul, seed='0x17')
        self.assertEqual( type(self.server.matmul(0x17)['SOMMATOIRE']),np.float64)


    def test_8(self):
        '''
         Runs all test against get_neofetch method

        :return: None
        '''

        self.assertRaises(TypeError, self.server.get_neofetch, greyscaeele='greyscale')
        self.assertEqual(type(self.server.get_neofetch()), str)


def _start_server():
    Pyro4.Daemon.serveSimple(
        {
            Server: "aniachi.image.process"

        },
        port=PORT,
        host="0.0.0.0",
        ns=False, verbose=True)


if __name__ == '__main__':
    '''
    Application entry point
    '''

    cheese = cow.www()
    msg = cheese.milk('Running server on port {0}'.format(PORT))
    print(msg, end='\n\n')
    _start_server()
