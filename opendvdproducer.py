#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, subprocess, time, random, codecs, tempfile, shutil, shutil,copy

from PySide import QtGui, QtCore
from PySide.phonon import Phonon

reload(sys)
sys.setdefaultencoding("utf-8")

if sys.platform == 'win32':
    path_opendvdproducer = getattr(sys, '_MEIPASS', os.getcwd())

else:
    path_opendvdproducer = os.path.dirname(sys.argv[0])

#os.path.realpath(__file__)#os.path.abspath(os.path.dirname(sys.argv[0]))

path_graphics = os.path.join(path_opendvdproducer, 'graphics')
path_home = os.path.expanduser("~")

path_tmp = os.path.join(tempfile.gettempdir(), 'opendvdproducer-' + str(random.randint(1000,9999)))

if sys.platform == 'darwin':
    iso2ddp_bin = os.path.join(path_opendvdproducer, 'iso2ddp_mac')
    imagemagick_convert_bin = os.path.join(path_opendvdproducer, 'convert')
    interface_font_size = 12
    ffprobe_bin = os.path.join(path_opendvdproducer, 'ffprobe')
    ffmpeg_bin = os.path.join(path_opendvdproducer,  'ffmpeg')
    spumux_bin = os.path.join(path_opendvdproducer, 'spumux')
    dvdauthor_bin = os.path.join(path_opendvdproducer, 'dvdauthor')
    mkisofs_bin = os.path.join(path_opendvdproducer, 'mkisofs')
    md5_bin = '/sbin/md5'
    split_bin = '/usr/bin/split'

elif sys.platform == 'win32':
    iso2ddp_bin = os.path.join(path_opendvdproducer, 'iso2ddp.exe')
    imagemagick_convert_bin = os.path.join(path_opendvdproducer, 'convert.exe')
    ffprobe_bin = os.path.join(path_opendvdproducer, 'ffprobe.exe')
    ffmpeg_bin = os.path.join(path_opendvdproducer, 'ffmpeg.exe')
    spumux_bin = os.path.join(path_opendvdproducer, 'spumux.exe')
    dvdauthor_bin = os.path.join(path_opendvdproducer, 'dvdauthor.exe')
    mkisofs_bin = os.path.join(path_opendvdproducer, 'mkisofs.exe')
    md5_bin = os.path.join(path_opendvdproducer, 'md5.exe')
    split_bin = os.path.join(path_opendvdproducer, 'split.exe')
    interface_font_size = 9
else:
    if subprocess.call("type ffprobe", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
        ffprobe_bin = 'ffprobe'
    else:
        ffprobe_bin = 'avprobe'
    if subprocess.call("type ffmpeg", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
        ffmpeg_bin = 'ffmpeg'
    else:
        ffmpeg_bin = 'avconv'
    spumux_bin = 'spumux'
    dvdauthor_bin = 'dvdauthor'
    mkisofs_bin = 'mkisofs'
    md5_bin = 'md5sum'
    split_bin = 'split'
    iso2ddp_bin = os.path.join(path_opendvdproducer, 'resources', 'iso2ddp')
    imagemagick_convert_bin = 'convert'
    interface_font_size = 10

os.mkdir(path_tmp)

class generate_dvd_thread_signal(QtCore.QObject):
    sig = QtCore.Signal(str)

class generate_dvd_thread(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.actual_project_file = ''
        self.project_name = 'Untitled'
        self.audio_codec = 'ac3'
        self.framerate = '25'
        self.height = 480
        self.video_format = 'pal'
        self.video_resolutions = ['720x480']
        self.aspect_ratio = '16:9'
        self.list_of_menus = []
        self.list_of_videos = []
        self.dict_of_menus = []
        self.dict_of_videos = []
        self.selected_gop_size = 12
        self.selected_menu_bitrate = 7500
        self.selected_menu_max_bitrate = 9000
        self.selected_video_bitrate = 7500
        self.selected_video_max_bitrate = 9000
        self.selected_menu_encoding = 'CBR'
        self.selected_video_encoding = 'CBR'
        self.selected_menu_twopass = True
        self.selected_video_twopass = True
        self.audio_datarate = 384
        self.generate_ddp = False
        self.generate_iso = True
        self.has_menus = True

        self.signal = generate_dvd_thread_signal()

    def run(self):
        def generate_ddp(original_file, output_path):
            split_area = 4699979776
            if os.path.getsize(original_file) < split_area:
                subprocess.call([iso2ddp_bin, '--inputfile=' + original_file, '--outputpath=' + output_path])
            else:
                subprocess.call([iso2ddp_bin, '--inputfile=' + original_file, '--layers=2', '--layer=1' '--outputpath=' + output_path])
                subprocess.call([iso2ddp_bin, '--inputfile=' + original_file, '--layers=2', '--layer=2' '--outputpath=' + output_path])

            output_path = output_path + '_TEST'

            sides = 1
            actual_side = 0
            disc_size = 'B' #Disc size "B" = 12cm, "A" = 8cm *
            tp_mode = "PTP"

            if os.path.getsize(original_file) < split_area:
                layers = ['Layer0']
            else:
                layers = ['Layer0', 'Layer1']

            if not os.path.isdir(output_path):
                subprocess.call(['mkdir', output_path])

            actual_layer = 0
            main_size = os.path.getsize(original_file)/2048
            for layer in layers:
                subprocess.call(['mkdir', os.path.join(output_path, layer)])

                if len(layers) == 1:
                    layer_size = main_size
                    layer0_size = main_size
                else:
                    layer0_size = split_area/2048
                    if actual_layer == 0:
                        layer_size = split_area/2048
                    else:
                        layer_size = main_size - (split_area/2048)

                ddpid = str(
                    "DDP 2.00" +
                    "             " +
                    "        " +
                    "        " +
                    " " +
                    "                                                " +
                    " " +
                    "DV" +
                    str(sides) +
                    str(actual_side) +
                    str(len(layers)) +
                    str(actual_layer) +
                    "I" +
                    disc_size +
                    "0" +
                    "0" +
                    "  " +
                    "                             " +

                    "VVVM" +
                    "D2" +
                    "        " +
                    "00000016" +
                    "00193024" +
                    "        " +
                    "DV" +
                    "1" +
                    "0" +
                    "    " +
                    "    " +
                    "    " +
                    " " +
                    "  " +
                    "  " +
                    "            " +
                    "017"
                    "CONTROL.DAT      " +
                    " " +
                    "    " +
                    "        " +
                    "         " +
                    "               " +

                    "VVVM" +
                    "D0" +
                    "        " +
                    str("%08d" % int(layer_size)) +
                    "00196608" +
                    "        " +
                    "DV" +
                    "0" +
                    "0" +
                    "    " +
                    "    " +
                    "    " +
                    " " +
                    "  " +
                    "  " +
                    "            " +
                    "017"
                    "MAIN.DAT         " +
                    " " +
                    "    " +
                    "        " +
                    "         " +
                    "               "
                    )

                open(os.path.join(output_path, layer, 'DDPID'), 'w').write(ddpid)

                control_dat = ''
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000001', 2)]))
                control_dat += str(bytearray([int('00000010', 2)]))

                if len(layers) == 2:
                    if tp_mode == "OTP":
                        control_dat += str(bytearray([int('00110001', 2)]))
                    else:
                        control_dat += str(bytearray([int('00100001', 2)]))
                else:
                    if tp_mode == "OTP":
                        control_dat += str(bytearray([int('00010001', 2)]))
                    else:
                        control_dat += str(bytearray([int('00000001', 2)]))

                control_dat += str(bytearray([int('00010000', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000011', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(bytearray([int('00000000', 2)]))
                control_dat += str(('%%0%dx' % (3 << 1) % int(196608 + main_size - 1)).decode('hex')[-3:])
                control_dat += str(bytearray([int('00000000', 2)]))

                if tp_mode == "OTP" and len(layers) == 2:
                    control_dat += str(('%%0%dx' % (3 << 1) % int(196608 + layer0_size - 1)).decode('hex')[-3:])
                else:
                    control_dat += str(bytearray([int('00000000', 2)]))
                    control_dat += str(bytearray([int('00000000', 2)]))
                    control_dat += str(bytearray([int('00000000', 2)]))

                control_dat += str(bytearray([int('00000000', 2)]))

                for i in range(16):
                    control_dat += str(bytearray([int('00000000', 2)]))

                for i in range(2015):
                    control_dat += str(bytearray([int('00000000', 2)]))

                for i in range(6):
                    control_dat += str(bytearray([int('00000000', 2)]))
                for i in range(2048):
                    control_dat += str(bytearray([int('00000000', 2)]))

                for i in range(14):
                    for j in range(6):
                        control_dat += str(bytearray([int('00000000', 2)]))
                    for j in range(2048):
                        control_dat += str(bytearray([int('00000000', 2)]))

                open(os.path.join(output_path, layer, 'CONTROL.DAT'), 'w').write(control_dat)

                actual_layer += 1

            if len(layers) == 2:
                subprocess.call([split_bin, '-b=' + str(split_area), os.path.join(path_tmp, 'movie.iso'), os.path.join(path_tmp, 'movie.iso_part')])
                shutil.move(os.path.join(path_tmp, 'movie.iso_part.aa'), os.path.join(output_path, 'Layer0', 'MAIN.DAT'))
                shutil.move(os.path.join(path_tmp, 'movie.iso_part.ab'), os.path.join(output_path, 'Layer1', 'MAIN.DAT'))
            else:
                shutil.copy(os.path.join(path_tmp, 'movie.iso'), os.path.join(output_path, 'Layer0', 'MAIN.DAT'))

        total_progress = str(len(self.list_of_videos) + len(self.list_of_menus) + 8)

        self.signal.sig.emit('START,0,' + total_progress)

        if not os.path.isdir(os.path.join(path_tmp, 'dvd')):
            os.mkdir(os.path.join(path_tmp, 'dvd'))

        final_dvd_author_xml = '<dvdauthor dest="' + os.path.join(path_tmp, 'dvd') + '">'

        list_of_used_videos = []
        for video in self.list_of_videos:
            list_of_used_videos.append(video)

        intro_video = False
        for video in self.list_of_videos:
            if self.dict_of_videos[video][3]:
                intro_video = video
                break

        final_dvd_author_xml += '<vmgm><menus><video format="' + self.video_format + '" aspect="' + self.aspect_ratio + '"'
        if self.aspect_ratio == '16:9':
            final_dvd_author_xml += ' widescreen="nopanscan"'
        final_dvd_author_xml += ' /><audio lang="EN" /><subpicture lang="EN" />'

        final_dvd_author_xml += '<pgc entry="title">'

        if intro_video:
            if self.dict_of_videos[intro_video][4]:
                video_path = os.path.join(path_tmp, intro_video + '.mpg')
            else:
                video_path = self.dict_of_videos[video][0]
                if self.has_menus:
                    final_dvd_author_xml += '<pre> if ( g0 != 0 ) jump titleset 1 menu; g0 = 1; </pre>'
                else:
                    final_dvd_author_xml += '<pre> if ( g0 != 0 ) jump titleset 1 title 1; g0 = 1; </pre>'
            final_dvd_author_xml += '<vob file="' + video_path + '"/>'
            list_of_used_videos.remove(intro_video)

        if self.has_menus:
            final_dvd_author_xml += '<post>jump titleset 1 menu;</post>'
        else:
            final_dvd_author_xml += '<post>jump title 1;</post>'

        final_dvd_author_xml += '</pgc></menus></vmgm>'
        final_dvd_author_xml += '<titleset>'

        menu_count = 1
        if self.has_menus:
            final_dvd_author_xml += '<menus>'

            final_dvd_author_xml += '<video format="' + self.video_format + '" aspect="' + self.aspect_ratio + '"'
            if self.aspect_ratio == '16:9':
                final_dvd_author_xml += ' widescreen="nopanscan"'
            final_dvd_author_xml += ' /><audio lang="EN" />'

            if self.aspect_ratio == '16:9':
                final_dvd_author_xml += '<subpicture lang="EN">'
                final_dvd_author_xml += '<stream id="0" mode="widescreen" /><stream id="1" mode="letterbox" />'
                final_dvd_author_xml += '</subpicture>'

            list_of_used_groups = []
            for video in list_of_used_videos:
                list_of_chapters = []
                for menu in self.list_of_menus:
                    for button in self.dict_of_menus[menu][1]:
                        if self.dict_of_menus[menu][2][button][4]:
                            if ' > ' in self.dict_of_menus[menu][2][button][4]:
                                if self.dict_of_menus[menu][2][button][4].split(' > ')[0] == video:
                                    if '(' in self.dict_of_menus[menu][2][button][4].split(' > ')[1]:
                                        list_of_chapters.append(self.dict_of_menus[menu][2][button][4].split(' > ')[1].split(' (')[1].split(')')[0])
                                    elif not self.dict_of_menus[menu][2][button][4] in list_of_used_groups:
                                        list_of_used_groups.append(self.dict_of_menus[menu][2][button][4])

            first_menu = True

            self.signal.sig.emit('PROCESSING MENUS,' + str(menu_count))

            for menu in self.list_of_menus:
                final_spumux_xml_0 = ''
                final_spumux_xml_1 = ''
                final_dvd_author_xml += '<pgc'
                if first_menu:
                    final_dvd_author_xml += ' entry="root"'
                    first_menu = False
                final_dvd_author_xml += '>'
                final_dvd_author_xml += '<vob file="' + os.path.join(path_tmp, menu + '_final.mpg') + '" />'

                if self.dict_of_menus[menu][0].split('.')[-1] == 'png':
                    if self.dict_of_menus[menu][5] and os.path.isfile(self.dict_of_menus[menu][5]):
                        sound_file = self.dict_of_menus[menu][5]
                    else:
                        sound_file = os.path.join(path_opendvdproducer, 'silence.flac')

                    sound_length_xml = unicode(subprocess.Popen([ffprobe_bin,'-loglevel', 'error',  '-show_format', '-print_format', 'xml', sound_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read(), 'utf-8')
                    print sound_length_xml
                    sound_length = float(sound_length_xml.split(' duration="')[1].split('"')[0])

                    final_command = [ffmpeg_bin]
                    final_command += '-y',
                    final_command += '-loop','1'
                    final_command += '-i', self.dict_of_menus[menu][0]
                    final_command += '-i', sound_file
                    final_command += '-c:v', 'mpeg2video'
                    final_command += '-c:a', self.audio_codec
                    final_command += '-f', 'dvd'
                    final_command += '-s', self.video_resolutions[0]
                    final_command += '-r', self.framerate
                    final_command += '-pix_fmt', 'yuv420p'
                    final_command += '-g', str(self.selected_gop_size)
                    final_command += '-b:v', str(self.selected_menu_bitrate * 1000)
                    if self.selected_menu_encoding == 'CBR':
                        final_command += '-maxrate', str(self.selected_menu_bitrate * 1000)
                        final_command += '-minrate', str(self.selected_menu_bitrate * 1000)
                    elif self.selected_menu_encoding == 'VBR':
                        final_command += '-maxrate', str(self.selected_menu_max_bitrate * 1000)
                        final_command += '-minrate', '0'
                    final_command += '-bufsize', '1835008'
                    final_command += '-packetsize', '2048'
                    final_command += '-muxrate', '10080000'
                    final_command += '-b:a', str(self.audio_datarate * 1000)
                    final_command += '-ar', '48000'
                    final_command += '-aspect', self.aspect_ratio
                    final_command += '-t', str(sound_length)
                    final_command += os.path.join(path_tmp, menu + '.mpg'),
                    subprocess.call(final_command)

                else:
                    final_command = [ffmpeg_bin]
                    final_command += '-y',
                    final_command += '-i', self.dict_of_menus[menu][0]
                    if self.selected_menu_twopass and self.selected_menu_encoding == 'VBR':
                        final_command += '-pass', '1'
                    final_command += '-c:v', 'mpeg2video'
                    final_command += '-c:a', self.audio_codec
                    final_command += '-f', 'dvd'
                    final_command += '-s', self.video_resolutions[0]
                    final_command += '-r', self.framerate
                    final_command += '-pix_fmt', 'yuv420p'
                    final_command += '-g', str(self.selected_gop_size)
                    final_command += '-b:v', str(self.selected_menu_bitrate * 1000)
                    if self.selected_menu_encoding == 'CBR':
                        final_command += '-maxrate', str(self.selected_menu_bitrate * 1000)
                        final_command += '-minrate', str(self.selected_menu_bitrate * 1000)
                    elif self.selected_menu_encoding == 'VBR':
                        final_command += '-maxrate', str(self.selected_menu_max_bitrate * 1000)
                        final_command += '-minrate', '0'
                    final_command += '-bufsize', '1835008'
                    final_command += '-packetsize', '2048'
                    final_command += '-muxrate', '10080000'
                    final_command += '-b:a', str(self.audio_datarate * 1000)
                    final_command += '-ar', '48000'
                    final_command += '-aspect', self.aspect_ratio
                    if self.selected_menu_twopass and self.selected_menu_encoding == 'VBR':
                        final_command += '-passlogfile', os.path.join(path_tmp, menu + '.log')
                    final_command += os.path.join(path_tmp, menu + '.mpg'),
                    subprocess.call(final_command)

                    if self.selected_menu_twopass and self.selected_menu_encoding == 'VBR':
                        final_command = [ffmpeg_bin]
                        final_command += '-y',
                        final_command += '-i', self.dict_of_menus[menu][0]
                        final_command += '-pass', '2'
                        final_command += '-c:v', 'mpeg2video'
                        final_command += '-c:a', self.audio_codec
                        final_command += '-f', 'dvd'
                        final_command += '-s', self.video_resolutions[0]
                        final_command += '-r', self.framerate
                        final_command += '-pix_fmt', 'yuv420p'
                        final_command += '-g', str(self.selected_gop_size)
                        final_command += '-b:v', str(self.selected_menu_bitrate * 1000)
                        if self.selected_menu_encoding == 'CBR':
                            final_command += '-maxrate', str(self.selected_menu_bitrate * 1000)
                            final_command += '-minrate', str(self.selected_menu_bitrate * 1000)
                        elif self.selected_menu_encoding == 'VBR':
                            final_command += '-maxrate', str(self.selected_menu_max_bitrate * 1000)
                            final_command += '-minrate', '0'
                        final_command += '-bufsize', '1835008'
                        final_command += '-packetsize', '2048'
                        final_command += '-muxrate', '10080000'
                        final_command += '-b:a', str(self.audio_datarate * 1000)
                        final_command += '-ar', '48000'
                        final_command += '-aspect', self.aspect_ratio
                        final_command += '-passlogfile', os.path.join(path_tmp, menu + '.log')
                        final_command += os.path.join(path_tmp, menu + '.mpg'),
                        subprocess.call(final_command)

                if self.dict_of_menus[menu][3]:
                    menu_color = '#FFFFFF'
                    if self.dict_of_menus[menu][4]:
                        menu_color = self.dict_of_menus[menu][4]
                    size = self.video_resolutions[0] + '!'
                    size_ws = self.video_resolutions[0].split('x')[0] + 'x' + str(self.height *.75) + '!'

                    subprocess.call([imagemagick_convert_bin, self.dict_of_menus[menu][3], '-resize', size, '+antialias', '-threshold', str(int(self.dict_of_menus[menu][8]*100)) + '%', '-flatten', os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_0.png')])
                    subprocess.call([imagemagick_convert_bin, os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_0.png'), '-threshold', str(int(self.dict_of_menus[menu][8]*100)) + '%', '-transparent', 'white', '-channel', 'RGBA', '-fill', menu_color + str('%02x' % int(self.dict_of_menus[menu][7]*255)), '-opaque', 'black', os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_0.png')])

                    subprocess.call([imagemagick_convert_bin, self.dict_of_menus[menu][3], '-resize', size_ws, '+antialias', '-threshold', str(int(self.dict_of_menus[menu][8]*100)) + '%', '-flatten', os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_1.png')])
                    subprocess.call([imagemagick_convert_bin, os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_1.png'), '-resize', size_ws, '-matte', '-bordercolor', 'none', '-border', '0x' + str( self.height * .125 ), os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_1.png')])
                    subprocess.call([imagemagick_convert_bin, os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_1.png'), '-threshold', str(int(self.dict_of_menus[menu][8]*100)) + '%', '-transparent', 'white', '-channel', 'RGBA', '-fill', menu_color + str('%02x' % int(self.dict_of_menus[menu][7]*255)), '-opaque', 'black', os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_1.png')])

                    final_spumux_xml_0 += '<subpictures><stream><spu force="yes" start="00:00:00.00" highlight="' + os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_0.png') + '">'
                    final_spumux_xml_1 += '<subpictures><stream><spu force="yes" start="00:00:00.00" highlight="' + os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl_1.png') + '">'

                for button in self.dict_of_menus[menu][1]:
                    if self.dict_of_menus[menu][2][button][4]:
                        final_dvd_author_xml += '<button name="' + button.replace(' ', '_') + '">jump '
                        jump_to = self.dict_of_menus[menu][2][button][4]
                        if jump_to in self.list_of_menus:
                            final_dvd_author_xml += 'menu ' + str(self.list_of_menus.index(jump_to) + 1) + ';'

                        elif not ' > ' in jump_to and jump_to in list_of_used_videos:
                            final_dvd_author_xml += 'title ' + str(list_of_used_videos.index(jump_to) + 1) + ';'

                        elif ' > ' in jump_to:
                            jump_to_video = jump_to.split(' > ')[0]
                            jump_to_mark = False
                            jumt_to_group = False
                            if '(' in jump_to.split(' > ')[1]:
                                jump_to_mark = jump_to.split(' > ')[1].split(' (')[0]
                            else:
                                jump_to_group = jump_to

                            if jump_to_mark:
                                if jump_to_video in list_of_used_videos and jump_to_mark in self.dict_of_videos[jump_to_video][1]:
                                    final_dvd_author_xml += 'title ' + str(list_of_used_videos.index(jump_to_video) + 1) + ' chapter ' + str(self.dict_of_videos[jump_to_video][1].index(jump_to_mark) + 1) + ';'
                            elif jump_to_group:
                                final_dvd_author_xml += 'title ' + str(len(list_of_used_videos) + list_of_used_groups.index(jump_to_group) + 1) + ';'

                        final_dvd_author_xml += '</button>'

                        if self.aspect_ratio == '16:9':
                            factor_x = 1
                            if self.video_format == 'pal':
                                factor_y = 1.42222222
                            elif self.video_format == 'ntsc':
                                factor_y = 1.18518519

                            x = int(int(self.dict_of_menus[menu][2][button][0]))
                            y = int(int(self.dict_of_menus[menu][2][button][1]))
                            w = int(int(self.dict_of_menus[menu][2][button][2]))
                            h = int(int(self.dict_of_menus[menu][2][button][3]))

                            final_spumux_xml_0 += '<button name="' + button.replace(' ', '_') + '" x0="' + str(x) + '" y0="' + str(y) + '" x1="' + str( x + w ) + '" y1="' + str( y + h ) + '"'
                            final_spumux_xml_1 += '<button name="' + button.replace(' ', '_') + '" x0="' + str(x) + '" y0="' + str(int( ( y * .75 ) + ( self.height * .125 ) )) + '" x1="' + str( x + w ) + '" y1="' + str(int( ( y * .75 ) + ( self.height * .125 ) + ( h * .75 ))) + '"'

                        if self.aspect_ratio == '4:3':
                            factor_x = 1.125
                            if self.video_format == 'pal':
                                factor_y = 1.2
                            elif self.video_format == 'ntsc':
                                factor_y = 1

                            x = int(int(self.dict_of_menus[menu][2][button][0]))
                            y = int(int(self.dict_of_menus[menu][2][button][1]))
                            w = int(int(self.dict_of_menus[menu][2][button][2]))
                            h = int(int(self.dict_of_menus[menu][2][button][3]))

                            final_spumux_xml_0 += '<button name="' + button.replace(' ', '_') + '" x0="' + str(int( x )) + '" y0="' + str(int( y )) + '" x1="' + str(int( x + w )) + '" y1="' + str(int( y + h )) + '"'

                        if self.dict_of_menus[menu][2][button][5][0]:
                            final_spumux_xml_0 += ' up="' + self.dict_of_menus[menu][2][button][5][0].replace(' ', '_') + '"'
                            final_spumux_xml_1 += ' up="' + self.dict_of_menus[menu][2][button][5][0].replace(' ', '_') + '"'
                        if self.dict_of_menus[menu][2][button][5][1]:
                            final_spumux_xml_0 += ' right="' + self.dict_of_menus[menu][2][button][5][1].replace(' ', '_') + '"'
                            final_spumux_xml_1 += ' right="' + self.dict_of_menus[menu][2][button][5][1].replace(' ', '_') + '"'
                        if self.dict_of_menus[menu][2][button][5][2]:
                            final_spumux_xml_0 += ' down="' + self.dict_of_menus[menu][2][button][5][2].replace(' ', '_') + '"'
                            final_spumux_xml_1 += ' down="' + self.dict_of_menus[menu][2][button][5][2].replace(' ', '_') + '"'
                        if self.dict_of_menus[menu][2][button][5][3]:
                            final_spumux_xml_0 += ' left="' + self.dict_of_menus[menu][2][button][5][3].replace(' ', '_') + '"'
                            final_spumux_xml_1 += ' left="' + self.dict_of_menus[menu][2][button][5][3].replace(' ', '_') + '"'

                        final_spumux_xml_0 += ' />'
                        final_spumux_xml_1 += ' />'
                final_dvd_author_xml += '<post>jump cell 1;</post>'
                final_dvd_author_xml += '</pgc>'
                final_spumux_xml_0 += '</spu></stream></subpictures>'
                final_spumux_xml_1 += '</spu></stream></subpictures>'

                if self.dict_of_menus[menu][3]:
                    open(os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_0.xml'), 'w').write(final_spumux_xml_0)
                    open(os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_1.xml'), 'w').write(final_spumux_xml_1)
                    menu_mpg_file = open(os.path.join(path_tmp, menu + '.mpg'))
                    menu_mpg_final_file = open(os.path.join(path_tmp, menu + '_final.mpg'), 'w')

                    if self.aspect_ratio == '16:9':
                        s0 = subprocess.Popen([spumux_bin, '-s', '0', os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_0.xml')],  stdin=menu_mpg_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        subprocess.call([spumux_bin, '-s', '1', os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_1.xml')],  stdin=s0.stdout, stdout=menu_mpg_final_file, stderr=subprocess.PIPE)
                        s0.stdout.close()
                    else:
                        subprocess.call([spumux_bin, os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_0.xml')],  stdin=menu_mpg_file, stdout=menu_mpg_final_file, stderr=subprocess.PIPE)
                    menu_mpg_final_file.close()

                else:
                    shutil.move(os.path.join(path_tmp, menu + '.mpg'), os.path.join(path_tmp, menu + '_final.mpg'))

                menu_count += 1
                self.signal.sig.emit('PROCESSING MENU' + menu.upper() + ',' + str(menu_count))

            final_dvd_author_xml += '</menus>'

        final_dvd_author_xml += '<titles>'

        self.signal.sig.emit('PROCESSING VIDEOS,' + str(menu_count + 1))

        video_count = menu_count + 1
        for video in self.list_of_videos:

            chapters_keyframes = ''
            for chapter in self.dict_of_videos[video][1]:
                chapters_keyframes += self.dict_of_videos[video][2][chapter] + ','

            print chapters_keyframes

            if self.dict_of_videos[video][4]:
                final_command = [ffmpeg_bin]
                final_command += '-y',
                final_command += '-i', self.dict_of_videos[video][0]
                if self.selected_video_twopass and self.selected_video_encoding == 'VBR':
                    final_command += '-pass', '1'
                final_command += '-c:v', 'mpeg2video'
                final_command += '-c:a', self.audio_codec
                final_command += '-f', 'dvd'
                final_command += '-s', self.video_resolutions[self.dict_of_videos[video][7]]
                final_command += '-r', self.framerate
                final_command += '-pix_fmt', 'yuv420p'
                final_command += '-g', str(self.selected_gop_size)
                if len(self.dict_of_videos[video][1]) > 0:
                    final_command += '-force_key_frames', chapters_keyframes[:-1]
                final_command += '-b:v', str(self.selected_video_bitrate * 1000)
                if self.selected_video_encoding == 'CBR':
                    final_command += '-maxrate', str(self.selected_video_bitrate * 1000)
                    final_command += '-minrate', str(self.selected_video_bitrate * 1000)
                elif self.selected_video_encoding == 'VBR':
                    final_command += '-maxrate', str(self.selected_video_max_bitrate * 1000)
                    final_command += '-minrate', '0'
                final_command += '-bufsize', '1835008'
                final_command += '-packetsize', '2048'
                final_command += '-muxrate', '10080000'
                final_command += '-b:a', str(self.audio_datarate * 1000)
                final_command += '-ar', '48000'
                final_command += '-aspect', self.aspect_ratio
                if self.selected_video_twopass and self.selected_video_encoding == 'VBR':
                    final_command += '-passlogfile', os.path.join(path_tmp, video + '.log')
                final_command += os.path.join(path_tmp, video + '.mpg'),
                subprocess.call(final_command)

                if self.selected_video_twopass and self.selected_video_encoding == 'VBR':
                    final_command = [ffmpeg_bin]
                    final_command += '-y',
                    final_command += '-i', self.dict_of_videos[video][0]
                    final_command += '-pass', '2'
                    final_command += '-c:v', 'mpeg2video'
                    final_command += '-c:a', self.audio_codec
                    final_command += '-f', 'dvd'
                    final_command += '-s', self.video_resolutions[self.dict_of_videos[video][7]]
                    final_command += '-r', self.framerate
                    final_command += '-pix_fmt', 'yuv420p'
                    final_command += '-g', str(self.selected_gop_size)
                    if len(self.dict_of_videos[video][1]) > 0:
                        final_command += '-force_key_frames', chapters_keyframes[:-1]#'chapters'
                    final_command += '-b:v', str(self.selected_video_bitrate * 1000)
                    if self.selected_video_encoding == 'CBR':
                        final_command += '-maxrate', str(self.selected_video_bitrate * 1000)
                        final_command += '-minrate', str(self.selected_video_bitrate * 1000)
                    elif self.selected_video_encoding == 'VBR':
                        final_command += '-maxrate', str(self.selected_video_max_bitrate * 1000)
                        final_command += '-minrate', '0'
                    final_command += '-bufsize', '1835008'
                    final_command += '-packetsize', '2048'
                    final_command += '-muxrate', '10080000'
                    final_command += '-b:a', str(self.audio_datarate * 1000)
                    final_command += '-ar', '48000'
                    final_command += '-aspect', self.aspect_ratio
                    final_command += '-passlogfile', os.path.join(path_tmp, video + '.log')
                    final_command += os.path.join(path_tmp, video + '.mpg'),
                    subprocess.call(final_command)

                video_path = os.path.join(path_tmp, video + '.mpg')
            else:
                video_path = self.dict_of_videos[video][0]

            if not self.dict_of_videos[video][3] and video in list_of_used_videos:
                final_dvd_author_xml += '<pgc>'
                final_dvd_author_xml += '<vob file="' + video_path + '"'

                if len(self.dict_of_videos[video][1]) > 0:
                    final_dvd_author_xml += ' chapters="'
                    final_dvd_author_xml += chapters_keyframes[:-1] + '"'
                final_dvd_author_xml += ' />'
                if self.has_menus:
                    final_dvd_author_xml += '<post>'
                    if self.dict_of_videos[video][6]:
                        jump_to = self.dict_of_videos[video][6]
                        if jump_to in self.list_of_menus:
                            final_dvd_author_xml += 'call menu ' + str(self.list_of_menus.index(jump_to) + 1) + ';'
                        elif not ' > ' in jump_to and jump_to in list_of_used_videos:
                            final_dvd_author_xml += 'jump title ' + str(list_of_used_videos.index(jump_to) + 1) + ';'
                    else:
                        final_dvd_author_xml += 'call menu;'
                    final_dvd_author_xml += '</post>'
                final_dvd_author_xml += '</pgc>'

            video_count += 1
            self.signal.sig.emit('PROCESSING VIDEO' + video.upper() + ',' + str(video_count))

        self.signal.sig.emit('PROCESSING GROUPS,' + str(video_count + 1))

        if self.has_menus:
            for group in list_of_used_groups:
                video = group.split(' > ')[0]

                final_dvd_author_xml += '<pgc>'

                if self.dict_of_videos[video][4]:
                    video_path = os.path.join(path_tmp, video + '.mpg')
                else:
                    video_path = self.dict_of_videos[video][0]

                final_dvd_author_xml += '<vob file="' + video_path + '">'

                temp_list_of_chapters = sort_list_of_chapters(self.dict_of_videos[video][2])
                temp_dict_of_chapters = self.dict_of_videos[video][2]

                if len(temp_list_of_chapters)%2 == 0:
                    length_xml = unicode(subprocess.Popen([ffprobe_bin, '-loglevel', 'error',  '-show_format', '-print_format', 'xml', self.dict_of_videos[video][0]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read(), 'utf-8')
                    length = convert_to_timecode(length_xml.split(' duration="')[1].split('"')[0], '1/1')
                    temp_dict_of_chapters['end'] = length
                    temp_list_of_chapters.append('end')

                for chapter in temp_list_of_chapters:
                    if chapter.split(' ')[0] == group.split(' > ')[1]:
                        mark = temp_dict_of_chapters[chapter]
                        next_mark = temp_dict_of_chapters[temp_list_of_chapters[temp_list_of_chapters.index(chapter)+1]]
                        final_dvd_author_xml += '<cell start="' +  mark + '" end="' + next_mark + '" chapter="1"></cell>'

                final_dvd_author_xml += '</vob>'
                final_dvd_author_xml += '<post>call menu;</post>'
                final_dvd_author_xml += '</pgc>'

        final_dvd_author_xml += '</titles></titleset>'

        final_dvd_author_xml += '</dvdauthor>'

        open(os.path.join(path_tmp, 'dvd.xml'), 'w').write(final_dvd_author_xml)

        self.signal.sig.emit('PROCESSING DVD FOLDERS,' + str(video_count + 2))

        subprocess.call([dvdauthor_bin, '-x', os.path.join(path_tmp, 'dvd.xml')])

        self.signal.sig.emit('PROCESSING DVD ISO,' + str(video_count + 3))

        subprocess.call([mkisofs_bin, '-v', '-dvd-video', '-udf', '-V', self.project_name[:32], '-o',  os.path.join(path_tmp, 'movie.iso'),  os.path.join(path_tmp, 'dvd')])
        if os.path.isfile(os.path.join(path_tmp, 'movie.iso')):
            self.signal.sig.emit('PROCESSING MD5,' + str(video_count + 4))

            md5 = subprocess.Popen([md5_bin, os.path.join(path_tmp, 'movie.iso')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()

            open(self.actual_project_file.replace(self.actual_project_file.split('/')[-1].split('\\')[-1], '') + self.project_name + '.md5', 'w').write(md5)

            if self.generate_ddp:
                self.signal.sig.emit('PROCESSING DDP,' + str(video_count + 5))
                generate_ddp(os.path.join(path_tmp, 'movie.iso'), self.actual_project_file.replace(self.actual_project_file.split('/')[-1].split('\\')[-1], '') + 'ddp')

            if self.generate_iso:
                shutil.move(os.path.join(path_tmp, 'movie.iso'), os.path.join(self.actual_project_file.replace(self.actual_project_file.split('/')[-1].split('\\')[-1], ''), self.project_name + '.iso'))
        else:
            print "NÃO GEROU ISO"

        shutil.rmtree(os.path.join(path_tmp, 'dvd'), ignore_errors=True)
        self.signal.sig.emit('FINISH')

class main_window(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Open DVD Producer')

        #self.setMaximumSize(self.width(), self.height())
        #self.setMinimumSize(self.width(), self.height())
        self.setWindowIcon(QtGui.QIcon(os.path.join(path_graphics, 'opendvdproducer.png')))
        self.move((QtGui.QDesktopWidget().screenGeometry().width()-self.geometry().width())/2, (QtGui.QDesktopWidget().screenGeometry().height()-self.geometry().height())/2)

        self.video_formats = ['PAL 720x576', 'NTSC 720x480']
        self.aspect_ratios = ['16:9', '4:3']
        self.audio_formats = ['MP2 48kHz', 'AC3 48kHz']
        self.resolutions = []

        self.main_panel = QtGui.QWidget(parent=self)

        self.content_panel = QtGui.QWidget(parent=self.main_panel)
        self.content_panel_animation = QtCore.QPropertyAnimation(self.content_panel, 'geometry')
        self.content_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.content_panel_background = QtGui.QLabel(parent=self.content_panel)
        self.content_panel_background.setPixmap(os.path.join(path_graphics, 'content_panel_background.png'))
        self.content_panel_background.setScaledContents(True)

        class preview(QtGui.QWidget):
            def paintEvent(widget, paintEvent):
                painter = QtGui.QPainter(widget)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)

                if self.selected_menu or not self.selected_menu_button_directioning == None:
                    pixmap = QtGui.QPixmap(os.path.join(path_tmp, self.selected_menu + '.preview.png'))
                    painter.drawPixmap(0,0,pixmap)

                    if len(self.dict_of_menus[self.selected_menu][1]) > 0:
                        if self.selected_aspect_ratio == 0:
                            factor_x = 1
                            if self.selected_video_format == 0:
                                factor_y = 0.703125
                            elif self.selected_video_format == 1:
                                factor_y = 0.84375
                        elif self.selected_aspect_ratio == 1:
                            factor_x = 0.88888888
                            if self.selected_video_format == 0:
                                factor_y = 0.833333333333
                            elif self.selected_video_format == 1:
                                factor_y = 1

                        for button in self.dict_of_menus[self.selected_menu][1]:
                            button_positions = [self.dict_of_menus[self.selected_menu][2][button][0]*factor_x, self.dict_of_menus[self.selected_menu][2][button][1]*factor_y, self.dict_of_menus[self.selected_menu][2][button][2]*factor_x, self.dict_of_menus[self.selected_menu][2][button][3]*factor_y]
                            painter.setPen(QtGui.QColor.fromRgb(0,0,0))
                            painter.setBrush(QtGui.QColor.fromRgb(0,0,0,a=0))
                            rectangle_main = QtCore.QRectF(button_positions[0], button_positions[1], button_positions[2], button_positions[3])
                            painter.drawRect(rectangle_main)

                            if button == self.selected_menu_button:
                                painter.setBrush(QtGui.QColor.fromRgb(80,80,80,a=200))
                                if self.overlay_preview and self.dict_of_menus[self.selected_menu][3]:
                                    overlay = QtGui.QPixmap(get_preview_file(self, os.path.join(path_tmp, self.dict_of_menus[self.selected_menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl.preview.png')))
                                    painter.setClipRect(rectangle_main)
                                    painter.drawPixmap(0,0,overlay)
                                    painter.setClipping(False)

                                painter.setPen(QtGui.QColor.fromRgb(0,0,0))
                                painter.setBrush(QtGui.QColor.fromRgb(0,0,0,a=0))

                                if self.directions_preview:
                                    direction_index = 0
                                    for direction in self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5]:
                                        if direction_index == 0:
                                            orig_x, orig_y =  (button_positions[0] + (button_positions[2]/2)), button_positions[1]
                                            if direction:
                                                dest_positions = [self.dict_of_menus[self.selected_menu][2][direction][0]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][1]*factor_y, self.dict_of_menus[self.selected_menu][2][direction][2]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][3]*factor_y]
                                                dest_x, dest_y =  (dest_positions[0] + (dest_positions[2]/2)), dest_positions[1] + dest_positions[3]
                                            elif not self.selected_menu_button_directioning == None:
                                                dest_x, dest_y =  self.selected_menu_button_directions[direction_index][0], self.selected_menu_button_directions[direction_index][1]
                                            else:
                                                dest_x, dest_y =  orig_x, orig_y - 20

                                            pen = QtGui.QPen(QtGui.QColor.fromRgb(0,0,0), 4)
                                            painter.setPen(pen)
                                            arrow_path = QtGui.QPainterPath(QtCore.QPointF(orig_x, orig_y))
                                            arrow_path.cubicTo(QtCore.QPointF(orig_x, orig_y-50), QtCore.QPointF(dest_x, dest_y+50), QtCore.QPointF(dest_x, dest_y + 8))
                                            painter.drawPath(arrow_path)
                                            pen = QtGui.QPen(QtCore.Qt.NoPen)
                                            painter.setPen(pen)
                                            arrow_path = QtGui.QPainterPath(QtCore.QPointF(dest_x + 5, dest_y + 8))
                                            arrow_path.lineTo(dest_x, dest_y)
                                            arrow_path.lineTo(dest_x - 5, dest_y + 8)
                                            arrow_path.lineTo(dest_x + 5, dest_y + 8)
                                            painter.fillPath(arrow_path, QtGui.QColor.fromRgb(0,0,0))

                                        elif direction_index == 1:
                                            orig_x, orig_y =  (button_positions[0] + button_positions[2]), (button_positions[1] + (button_positions[3]/2))
                                            if direction:
                                                dest_positions = [self.dict_of_menus[self.selected_menu][2][direction][0]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][1]*factor_y, self.dict_of_menus[self.selected_menu][2][direction][2]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][3]*factor_y]
                                                dest_x, dest_y =  dest_positions[0], (dest_positions[1] + (dest_positions[3]/2))
                                            elif not self.selected_menu_button_directioning == None:
                                                dest_x, dest_y =  self.selected_menu_button_directions[direction_index][0], self.selected_menu_button_directions[direction_index][1]
                                            else:
                                                dest_x, dest_y =  orig_x + 20, orig_y
                                            pen = QtGui.QPen(QtGui.QColor.fromRgb(0,0,0), 4)
                                            painter.setPen(pen)
                                            arrow_path = QtGui.QPainterPath(QtCore.QPointF(orig_x, orig_y))
                                            arrow_path.cubicTo(QtCore.QPointF(orig_x+50, orig_y), QtCore.QPointF(dest_x-50, dest_y), QtCore.QPointF(dest_x - 8, dest_y))
                                            painter.drawPath(arrow_path)
                                            pen = QtGui.QPen(QtCore.Qt.NoPen)
                                            painter.setPen(pen)
                                            arrow_path = QtGui.QPainterPath(QtCore.QPointF(dest_x - 8, dest_y + 5))
                                            arrow_path.lineTo(dest_x, dest_y)
                                            arrow_path.lineTo(dest_x - 8, dest_y - 5)
                                            arrow_path.lineTo(dest_x - 8, dest_y + 5)
                                            painter.fillPath(arrow_path, QtGui.QColor.fromRgb(0,0,0))

                                        elif direction_index == 2:
                                            orig_x, orig_y =  button_positions[0] + (button_positions[2]/2), button_positions[1] + button_positions[3]
                                            if direction:
                                                dest_positions = [self.dict_of_menus[self.selected_menu][2][direction][0]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][1]*factor_y, self.dict_of_menus[self.selected_menu][2][direction][2]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][3]*factor_y]
                                                dest_x, dest_y =  (dest_positions[0] + (dest_positions[2]/2)), dest_positions[1]
                                            elif not self.selected_menu_button_directioning == None:
                                                dest_x, dest_y =  self.selected_menu_button_directions[direction_index][0], self.selected_menu_button_directions[direction_index][1]
                                            else:
                                                dest_x, dest_y =  orig_x, orig_y + 20
                                            pen = QtGui.QPen(QtGui.QColor.fromRgb(0,0,0), 4)
                                            painter.setPen(pen)
                                            arrow_path = QtGui.QPainterPath(QtCore.QPointF(orig_x, orig_y))
                                            arrow_path.cubicTo(QtCore.QPointF(orig_x, orig_y+50), QtCore.QPointF(dest_x, dest_y-50), QtCore.QPointF(dest_x, dest_y - 8))
                                            painter.drawPath(arrow_path)
                                            pen = QtGui.QPen(QtCore.Qt.NoPen)
                                            painter.setPen(pen)
                                            arrow_path = QtGui.QPainterPath(QtCore.QPointF(dest_x + 5, dest_y - 8))
                                            arrow_path.lineTo(dest_x, dest_y)
                                            arrow_path.lineTo(dest_x - 5, dest_y - 8)
                                            arrow_path.lineTo(dest_x + 5, dest_y - 8)
                                            painter.fillPath(arrow_path, QtGui.QColor.fromRgb(0,0,0))

                                        elif direction_index == 3:
                                            orig_x, orig_y =  button_positions[0], (button_positions[1] + (button_positions[3]/2))
                                            if direction:
                                                dest_positions = [self.dict_of_menus[self.selected_menu][2][direction][0]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][1]*factor_y, self.dict_of_menus[self.selected_menu][2][direction][2]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][3]*factor_y]
                                                dest_x, dest_y =  (dest_positions[0] + dest_positions[2]), (dest_positions[1] + (dest_positions[3]/2))
                                            elif not self.selected_menu_button_directioning == None:
                                                dest_x, dest_y =  self.selected_menu_button_directions[direction_index][0], self.selected_menu_button_directions[direction_index][1]
                                            else:
                                                dest_x, dest_y =  orig_x - 20, orig_y
                                            pen = QtGui.QPen(QtGui.QColor.fromRgb(0,0,0), 4)
                                            painter.setPen(pen)
                                            arrow_path = QtGui.QPainterPath(QtCore.QPointF(orig_x, orig_y))
                                            arrow_path.cubicTo(QtCore.QPointF(orig_x-50, orig_y), QtCore.QPointF(dest_x+50, dest_y), QtCore.QPointF(dest_x + 8, dest_y))
                                            painter.drawPath(arrow_path)
                                            pen = QtGui.QPen(QtCore.Qt.NoPen)
                                            painter.setPen(pen)
                                            arrow_path = QtGui.QPainterPath(QtCore.QPointF(dest_x + 8, dest_y - 5))
                                            arrow_path.lineTo(dest_x, dest_y)
                                            arrow_path.lineTo(dest_x + 8, dest_y + 5)
                                            arrow_path.lineTo(dest_x + 8, dest_y - 5)
                                            painter.fillPath(arrow_path, QtGui.QColor.fromRgb(0,0,0))

                                        painter.drawPath(arrow_path)
                                        direction_index += 1

                                painter.setPen(QtGui.QColor.fromRgb(0,0,0))
                                painter.setBrush(QtGui.QColor.fromRgb(80,80,80,a=200))

                            else:
                                painter.setBrush(QtGui.QColor.fromRgb(0,0,0))

                            rectangle = QtCore.QRectF(button_positions[0]-5, button_positions[1]-5, painter.fontMetrics().width(button) + 5,10)
                            painter.drawRoundedRect(rectangle, 5,5)
                            painter.setPen(QtGui.QColor.fromRgb(255,255,255))
                            painter.setFont(QtGui.QFont('Ubuntu', interface_font_size*.8))
                            rectangle = QtCore.QRectF(button_positions[0]-3, button_positions[1]-6, painter.fontMetrics().width(button) + 5,10)
                            painter.drawText(rectangle, QtCore.Qt.AlignLeft, button)
                            rectangle = QtCore.QRectF(button_positions[2]+button_positions[0]-5, button_positions[3]+button_positions[1]-5, 10,10)
                            painter.setBrush(QtGui.QColor.fromRgb(0,0,0))
                            painter.drawEllipse(rectangle)

                else:
                    pixmap = QtGui.QPixmap(os.path.join(path_graphics, 'preview_' + str(self.aspect_ratios[self.selected_aspect_ratio]).replace(':', '_') + '_space.png'))
                    painter.drawPixmap(0,0,pixmap)

                painter.end()

            def mousePressEvent(widget, event):
                if self.selected_aspect_ratio == 0:
                    factor_x = 1
                    if self.selected_video_format == 0:
                        factor_y = 0.703125
                    elif self.selected_video_format == 1:
                        factor_y = 0.84375
                elif self.selected_aspect_ratio == 1:
                    factor_x = 0.88888888
                    if self.selected_video_format == 0:
                        factor_y = 0.833333333333
                    elif self.selected_video_format == 1:
                        factor_y = 1


                if self.selected_menu_button and self.directions_preview:#self.selected_menu_button_directioning
                    button_positions = [self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][0]*factor_x, self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][1]*factor_y, self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][2]*factor_x, self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][3]*factor_y]
                    direction_index = 0
                    for direction in self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5]:
                        if direction_index == 0:
                            if direction:
                                dest_positions = [self.dict_of_menus[self.selected_menu][2][direction][0]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][1]*factor_y, self.dict_of_menus[self.selected_menu][2][direction][2]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][3]*factor_y]
                                self.selected_menu_button_directions[direction_index] = [dest_positions[0] + (dest_positions[2]/2), dest_positions[1] + dest_positions[3]]
                            else:
                                orig_x, orig_y =  button_positions[0] + (button_positions[2]/2), button_positions[1]
                                self.selected_menu_button_directions[direction_index] = [orig_x, orig_y - 20]

                        elif direction_index == 1:
                            if direction:
                                dest_positions = [self.dict_of_menus[self.selected_menu][2][direction][0]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][1]*factor_y, self.dict_of_menus[self.selected_menu][2][direction][2]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][3]*factor_y]
                                self.selected_menu_button_directions[direction_index] = [dest_positions[0], (dest_positions[1] + (dest_positions[3]/2))]
                            else:
                                orig_x, orig_y =  button_positions[0] + button_positions[2], button_positions[1] + (button_positions[3]/2)
                                self.selected_menu_button_directions[direction_index] = [orig_x + 20, orig_y]

                        elif direction_index == 2:
                            if direction:
                                dest_positions = [self.dict_of_menus[self.selected_menu][2][direction][0]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][1]*factor_y, self.dict_of_menus[self.selected_menu][2][direction][2]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][3]*factor_y]
                                self.selected_menu_button_directions[direction_index] = [dest_positions[0] + (dest_positions[2]/2), dest_positions[1]]
                            else:
                                orig_x, orig_y =  button_positions[0] + (button_positions[2]/2), button_positions[1] + button_positions[3]
                                self.selected_menu_button_directions[direction_index] = [orig_x, orig_y + 20]

                        elif direction_index == 3:
                            if direction:
                                dest_positions = [self.dict_of_menus[self.selected_menu][2][direction][0]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][1]*factor_y, self.dict_of_menus[self.selected_menu][2][direction][2]*factor_x, self.dict_of_menus[self.selected_menu][2][direction][3]*factor_y]
                                self.selected_menu_button_directions[direction_index] = [dest_positions[0] + dest_positions[2], (dest_positions[1] + (dest_positions[3]/2))]
                            else:
                                orig_x, orig_y =  button_positions[0], button_positions[1] + (button_positions[3]/2)
                                self.selected_menu_button_directions[direction_index] = [orig_x - 20, orig_y]

                        direction_index += 1

                    if   (((event.pos().x() > self.selected_menu_button_directions[0][0] - 6)  and (event.pos().x() < self.selected_menu_button_directions[0][0] + 6))  and ((event.pos().y() > self.selected_menu_button_directions[0][1] - 1)  and (event.pos().y() < self.selected_menu_button_directions[0][1]  + 11))):
                        self.selected_menu_button_directioning = 0
                    elif (((event.pos().x() > self.selected_menu_button_directions[1][0] - 11) and (event.pos().x() < self.selected_menu_button_directions[1][0] + 1))  and ((event.pos().y() > self.selected_menu_button_directions[1][1] - 6)  and (event.pos().y() < self.selected_menu_button_directions[1][1]  + 6))):
                        self.selected_menu_button_directioning = 1
                    elif (((event.pos().x() > self.selected_menu_button_directions[2][0] - 6)  and (event.pos().x() < self.selected_menu_button_directions[2][0] + 6))  and ((event.pos().y() > self.selected_menu_button_directions[2][1] - 11) and (event.pos().y() < self.selected_menu_button_directions[2][1]  + 1))):
                        self.selected_menu_button_directioning = 2
                    elif (((event.pos().x() > self.selected_menu_button_directions[3][0] - 1)  and (event.pos().x() < self.selected_menu_button_directions[3][0] + 11)) and ((event.pos().y() > self.selected_menu_button_directions[3][1] - 6)  and (event.pos().y() < self.selected_menu_button_directions[3][1]  + 6))):
                        self.selected_menu_button_directioning = 3
                    else:
                        self.selected_menu_button_directioning = None

                if self.selected_menu_button_directioning == None:
                    self.selected_menu_button = None

                self.selected_menu_button_resizing = False

                if self.selected_menu:
                    for button in self.dict_of_menus[self.selected_menu][1]:
                        button_positions = [self.dict_of_menus[self.selected_menu][2][button][0]*factor_x, self.dict_of_menus[self.selected_menu][2][button][1]*factor_y, self.dict_of_menus[self.selected_menu][2][button][2]*factor_x, self.dict_of_menus[self.selected_menu][2][button][3]*factor_y]
                        if self.selected_menu_button_directioning == None:
                            if ((event.pos().x() > button_positions[0]-5) and (event.pos().x() < button_positions[0] + button_positions[2] + 5)) and ((event.pos().y() > button_positions[1]-5) and (event.pos().y() < button_positions[1] + button_positions[3] + 5)):
                                self.selected_menu_button = button
                                self.selected_menu_button_preview_difference = [event.pos().x() - button_positions[0],event.pos().y() - button_positions[1]]
                                self.options_panel_menu_buttons.setCurrentRow(self.dict_of_menus[self.selected_menu][1].index(self.selected_menu_button))
                                menu_button_selected(self)
                                if ((event.pos().x() > button_positions[0] + button_positions[2] - 5) and (event.pos().x() < button_positions[0] + button_positions[2] + 5)) and ((event.pos().y() > button_positions[1] + button_positions[3] - 5) and (event.pos().y() < button_positions[1] + button_positions[3] + 5)):
                                    self.selected_menu_button_resizing = True

                if not self.selected_menu_button:
                    clean_buttons_selection(self)

            def mouseReleaseEvent(widget, event):
                self.selected_menu_button_preview_difference = [0,0]
                update_changes(self)

            def mouseMoveEvent(widget, event):
                if self.selected_menu_button:
                    button_positions = self.dict_of_menus[self.selected_menu][2][self.selected_menu_button]

                    if self.selected_aspect_ratio == 0:
                        factor_x = 1
                        if self.selected_video_format == 0:
                            factor_y = 1.42222222
                        elif self.selected_video_format == 1:
                            factor_y = 1.18518519
                    elif self.selected_aspect_ratio == 1:
                        factor_x = 1.125
                        if self.selected_video_format == 0:
                            factor_y = 1.2
                        elif self.selected_video_format == 1:
                            factor_y = 1

                    if not self.selected_menu_button_directioning == None and self.directions_preview:
                        final_x = int( event.pos().x() * factor_x )
                        final_y = int( event.pos().y() * factor_y )
                        for button in self.dict_of_menus[self.selected_menu][1]:
                            if not self.selected_menu_button == button:
                                dest_positions = [self.dict_of_menus[self.selected_menu][2][button][0], self.dict_of_menus[self.selected_menu][2][button][1], self.dict_of_menus[self.selected_menu][2][button][2], self.dict_of_menus[self.selected_menu][2][button][3]]
                                if ((final_x > dest_positions[0]-5) and (final_x < dest_positions[0] + dest_positions[2] + 5)) and ((final_y > dest_positions[1]-5) and (final_y < dest_positions[1] + dest_positions[3] + 5)):
                                    self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][self.selected_menu_button_directioning] = button
                                    break
                                else:
                                    self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][self.selected_menu_button_directioning] = None
                        self.selected_menu_button_directions[self.selected_menu_button_directioning][0] = int(event.pos().x())
                        self.selected_menu_button_directions[self.selected_menu_button_directioning][1] = int(event.pos().y())
                    else:
                        if self.selected_menu_button_resizing:
                            button_positions[2] = int( event.pos().x() * factor_x) - button_positions[0]
                            button_positions[3] = int( event.pos().y() * factor_y) - button_positions[1]
                        else:
                            button_positions[0] = int( int(event.pos().x() - self.selected_menu_button_preview_difference[0]) ) * factor_x
                            button_positions[1] = int( int(event.pos().y() - self.selected_menu_button_preview_difference[1]) ) * factor_y

                        self.dict_of_menus[self.selected_menu][2][self.selected_menu_button] = button_positions
                    update_changes(self)

        self.preview = preview(parent=self.content_panel)

        self.no_preview_label = QtGui.QLabel(parent=self.preview)
        self.no_preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.no_preview_label.setForegroundRole(QtGui.QPalette.Midlight)

        self.preview_video_obj = Phonon.MediaObject(parent=self)
        self.preview_video_obj.setTickInterval(200)
        self.preview_video_obj.tick.connect(lambda:update_timeline(self))
        self.preview_video_widget = Phonon.VideoWidget(parent=self.main_panel)
        self.preview_video_audio = Phonon.AudioOutput(Phonon.VideoCategory, self)

        Phonon.createPath(self.preview_video_obj, self.preview_video_audio)
        Phonon.createPath(self.preview_video_obj, self.preview_video_widget)

        self.options_panel = QtGui.QWidget(parent=self.content_panel)
        self.options_panel_animation = QtCore.QPropertyAnimation(self.options_panel, 'geometry')
        self.options_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.options_panel_background = QtGui.QLabel(parent=self.options_panel)
        self.options_panel_background.setPixmap(os.path.join(path_graphics, 'options_panel_background.png'))
        self.options_panel_background.setScaledContents(True)

        self.options_panel_dvd_panel = QtGui.QWidget(parent=self.options_panel)

        class options_panel_dvd_panel_dvd_image(QtGui.QWidget):
            def paintEvent(widget, paintEvent):
                estimated_size = 0.0

                if len(self.list_of_videos) > 0:
                    if self.has_menus and len(self.list_of_menus) > 0:
                        for menu in self.list_of_menus:
                            estimated_size += float(((self.selected_menu_bitrate + int(self.selected_audio_datarate.split(' ')[0]))*.00001) * self.dict_of_menus[menu][9])
                    for video in self.list_of_videos:
                        estimated_size += float(((self.selected_video_bitrate + int(self.selected_audio_datarate.split(' ')[0]))*.00001) * self.dict_of_videos[video][5])

                painter = QtGui.QPainter(widget)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)

                pen = QtGui.QPen(QtCore.Qt.NoPen)
                painter.setPen(pen)

                painter.setBrush(QtGui.QColor.fromRgb(0,0,0,a=50))
                rectangle = QtCore.QRectF(28,28,244,244)
                rectangle_inner = QtCore.QRectF(106,106,88,88)

                def get_inner_point(angle):
                    circle_inner_path = QtGui.QPainterPath()
                    circle_inner_path.arcTo(rectangle_inner,90, angle)
                    return circle_inner_path.currentPosition()

                if estimated_size > 360.0:
                    circle_path = QtGui.QPainterPath()
                    circle_path.arcMoveTo(rectangle, 90)
                    circle_path.arcTo(rectangle, 90, 359.9)
                    circle_path.lineTo(get_inner_point(359.9))
                    circle_path.arcTo(rectangle_inner, 90 + 359.9, 359.9 * (-1))
                    circle_path.closeSubpath()
                    painter.drawPath(circle_path)
                    estimated_size -= 360

                circle_path = QtGui.QPainterPath()
                circle_path.arcMoveTo(rectangle, 90)
                circle_path.arcTo(rectangle, 90, estimated_size)
                circle_path.lineTo(get_inner_point(estimated_size))
                circle_path.arcTo(rectangle_inner, 90 + estimated_size, estimated_size * (-1))
                circle_path.closeSubpath()
                painter.drawPath(circle_path)

                foreground = QtGui.QPixmap(os.path.join(path_graphics, 'options_panel_dvd_image_background.png'))
                painter.drawPixmap(0,0,foreground)

        self.options_panel_dvd_panel_dvd_image = options_panel_dvd_panel_dvd_image(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_dvd_image.setGeometry(35,0,300,300)

        self.options_panel_dvd_panel_size_info = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_size_info.setGeometry(35,300,300,40)
        self.options_panel_dvd_panel_size_info.setAlignment(QtCore.Qt.AlignCenter)

        self.options_panel_dvd_panel_menu_encoding_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_encoding_label.setGeometry(10, 360, 170, 20)
        self.options_panel_dvd_panel_menu_encoding_label.setText('MENU ENCODING')

        class options_panel_dvd_panel_menu_encoding(QtGui.QWidget):
            def mousePressEvent(widget, event):
                options_panel_dvd_panel_menu_encoding_changed(self)

        self.options_panel_dvd_panel_menu_encoding = options_panel_dvd_panel_menu_encoding(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_encoding.setGeometry(10, 380, 78, 25)

        self.options_panel_dvd_panel_menu_encoding_background = QtGui.QLabel(parent=self.options_panel_dvd_panel_menu_encoding)
        self.options_panel_dvd_panel_menu_encoding_background.setGeometry(0,0,self.options_panel_dvd_panel_menu_encoding.width(),self.options_panel_dvd_panel_menu_encoding.height())

        self.options_panel_dvd_panel_menu_bitrate_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_bitrate_label.setGeometry(10, 415, 170, 20)
        self.options_panel_dvd_panel_menu_bitrate_label.setText('MENU BITRATE')

        self.options_panel_dvd_panel_menu_bitrate_field = QtGui.QSpinBox(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_bitrate_field.setGeometry(10, 435, 100, 30)
        self.options_panel_dvd_panel_menu_bitrate_field.setMinimum(1000)
        self.options_panel_dvd_panel_menu_bitrate_field.setMaximum(9600)
        self.options_panel_dvd_panel_menu_bitrate_field.editingFinished.connect(lambda:options_panel_dvd_panel_bitrates_changed(self))

        self.options_panel_dvd_panel_menu_bitrate_field_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_bitrate_field_label.setGeometry(115, 435, 65, 30)
        self.options_panel_dvd_panel_menu_bitrate_field_label.setText('Kbp/s')

        self.options_panel_dvd_panel_menu_max_bitrate_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_max_bitrate_label.setGeometry(10, 475, 170, 20)
        self.options_panel_dvd_panel_menu_max_bitrate_label.setText('MENU MAXIMUM BITRATE')

        self.options_panel_dvd_panel_menu_max_bitrate_field = QtGui.QSpinBox(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_max_bitrate_field.setGeometry(10, 495, 100, 30)
        self.options_panel_dvd_panel_menu_max_bitrate_field.setMinimum(1000)
        self.options_panel_dvd_panel_menu_max_bitrate_field.setMaximum(9600)
        self.options_panel_dvd_panel_menu_max_bitrate_field.editingFinished.connect(lambda:options_panel_dvd_panel_bitrates_changed(self))

        self.options_panel_dvd_panel_menu_max_bitrate_field_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_max_bitrate_field_label.setGeometry(115, 495, 65, 30)
        self.options_panel_dvd_panel_menu_max_bitrate_field_label.setText('Kbp/s')

        self.options_panel_dvd_panel_menu_twopass_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_twopass_label.setGeometry(10, 535, 170, 20)
        self.options_panel_dvd_panel_menu_twopass_label.setText('PASSES')

        class options_panel_dvd_panel_menu_twopass(QtGui.QWidget):
            def mousePressEvent(widget, event):
                options_panel_dvd_panel_menu_twopass_changed(self)

        self.options_panel_dvd_panel_menu_twopass = options_panel_dvd_panel_menu_twopass(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_menu_twopass.setGeometry(10, 555, 78,25)

        self.options_panel_dvd_panel_menu_twopass_background = QtGui.QLabel(parent=self.options_panel_dvd_panel_menu_twopass)
        self.options_panel_dvd_panel_menu_twopass_background.setGeometry(0,0,self.options_panel_dvd_panel_menu_twopass.width(),self.options_panel_dvd_panel_menu_twopass.height())

        self.options_panel_dvd_panel_video_encoding_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_encoding_label.setGeometry(190, 360, 170, 20)
        self.options_panel_dvd_panel_video_encoding_label.setText('VIDEO ENCODING')

        class options_panel_dvd_panel_video_encoding(QtGui.QWidget):
            def mousePressEvent(widget, event):
                options_panel_dvd_panel_video_encoding_changed(self)

        self.options_panel_dvd_panel_video_encoding = options_panel_dvd_panel_video_encoding(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_encoding.setGeometry(190, 380, 78, 25)

        self.options_panel_dvd_panel_video_encoding_background = QtGui.QLabel(parent=self.options_panel_dvd_panel_video_encoding)
        self.options_panel_dvd_panel_video_encoding_background.setGeometry(0,0,self.options_panel_dvd_panel_video_encoding.width(),self.options_panel_dvd_panel_video_encoding.height())

        self.options_panel_dvd_panel_video_bitrate_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_bitrate_label.setGeometry(190, 415, 170, 20)
        self.options_panel_dvd_panel_video_bitrate_label.setText('VIDEO BITRATE')

        self.options_panel_dvd_panel_video_bitrate_field = QtGui.QSpinBox(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_bitrate_field.setGeometry(190, 435, 100, 30)
        self.options_panel_dvd_panel_video_bitrate_field.setMinimum(1000)
        self.options_panel_dvd_panel_video_bitrate_field.setMaximum(9600)
        self.options_panel_dvd_panel_video_bitrate_field.editingFinished.connect(lambda:options_panel_dvd_panel_bitrates_changed(self))

        self.options_panel_dvd_panel_video_bitrate_field_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_bitrate_field_label.setGeometry(295, 435, 65, 30)
        self.options_panel_dvd_panel_video_bitrate_field_label.setText('Kbp/s')

        self.options_panel_dvd_panel_video_max_bitrate_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_max_bitrate_label.setGeometry(190, 475, 170, 20)
        self.options_panel_dvd_panel_video_max_bitrate_label.setText('VIDEO MAXIMUM BITRATE')

        self.options_panel_dvd_panel_video_max_bitrate_field = QtGui.QSpinBox(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_max_bitrate_field.setGeometry(190, 495, 100, 30)
        self.options_panel_dvd_panel_video_max_bitrate_field.setMinimum(1000)
        self.options_panel_dvd_panel_video_max_bitrate_field.setMaximum(9600)
        self.options_panel_dvd_panel_video_max_bitrate_field.editingFinished.connect(lambda:options_panel_dvd_panel_bitrates_changed(self))

        self.options_panel_dvd_panel_video_max_bitrate_field_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_max_bitrate_field_label.setGeometry(295, 495, 65, 30)
        self.options_panel_dvd_panel_video_max_bitrate_field_label.setText('Kbp/s')


        self.options_panel_dvd_panel_video_twopass_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_twopass_label.setGeometry(190, 535, 170, 20)
        self.options_panel_dvd_panel_video_twopass_label.setText('PASSES')

        class options_panel_dvd_panel_video_twopass(QtGui.QWidget):
            def mousePressEvent(widget, event):
                options_panel_dvd_panel_video_twopass_changed(self)

        self.options_panel_dvd_panel_video_twopass = options_panel_dvd_panel_video_twopass(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_video_twopass.setGeometry(190, 555, 78, 25)

        self.options_panel_dvd_panel_video_twopass_background = QtGui.QLabel(parent=self.options_panel_dvd_panel_video_twopass)
        self.options_panel_dvd_panel_video_twopass_background.setGeometry(0,0,self.options_panel_dvd_panel_video_twopass.width(),self.options_panel_dvd_panel_video_twopass.height())

        self.options_panel_dvd_panel_gop_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_gop_label.setGeometry(10, 600, 170, 20)
        self.options_panel_dvd_panel_gop_label.setText('GOP SIZE')

        self.options_panel_dvd_panel_gop = QtGui.QComboBox(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_gop.setGeometry(10, 620, 170, 30)
        self.options_panel_dvd_panel_gop.addItems(['6','7','8','9','10','11', '12','13','14','15'])
        self.options_panel_dvd_panel_gop.activated.connect(lambda:options_panel_dvd_panel_gop_changed(self))

        self.options_panel_dvd_panel_audio_datarate_label = QtGui.QLabel(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_audio_datarate_label.setGeometry(190, 600, 170, 20)
        self.options_panel_dvd_panel_audio_datarate_label.setText('AUDIO DATA RATE')

        self.options_panel_dvd_panel_audio_datarate = QtGui.QComboBox(parent=self.options_panel_dvd_panel)
        self.options_panel_dvd_panel_audio_datarate.setGeometry(190, 620, 170, 30)
        self.options_panel_dvd_panel_audio_datarate.addItems(['4608 kb/s (24/96)','3072 kb/s (16/96)','2304 kb/s (24/48)','1536 kb/s (DVD PCM)','512 kb/s','448 kb/s','384 kb/s','256 kb/s','224 kb/s (VCD MPA)','192 kb/s','160 kb/s','128 kb/s'])
        self.options_panel_dvd_panel_audio_datarate.activated.connect(lambda:options_panel_dvd_panel_audio_datarate_changed(self))

        self.options_panel_menu_panel = QtGui.QWidget(parent=self.options_panel)

        self.options_panel_menu_buttons_label = QtGui.QLabel('BUTTONS', parent=self.options_panel_menu_panel)

        self.options_panel_menu_buttons = QtGui.QListWidget(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons.clicked.connect(lambda:menu_button_selected(self))

        self.options_panel_menu_buttons_add = QtGui.QPushButton(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_add.setGeometry(10,245,30,30)
        self.options_panel_menu_buttons_add.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'add.png')))
        self.options_panel_menu_buttons_add.clicked.connect(lambda:add_menu_button(self))

        self.options_panel_menu_buttons_remove = QtGui.QPushButton(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_remove.setGeometry(45,245,30,30)
        self.options_panel_menu_buttons_remove.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'remove.png')))
        self.options_panel_menu_buttons_remove.clicked.connect(lambda:remove_menu_button(self))
        self.options_panel_menu_buttons_remove.setEnabled(False)

        self.options_panel_menu_buttons_edit = QtGui.QPushButton(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_edit.setGeometry(80,245,30,30)
        self.options_panel_menu_buttons_edit.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'edit.png')))
        self.options_panel_menu_buttons_edit.clicked.connect(lambda:edit_menu_button(self))
        self.options_panel_menu_buttons_edit.setEnabled(False)

        self.options_panel_menu_buttons_edit_field = QtGui.QLineEdit(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_edit_field.textEdited.connect(lambda:edit_field_menu_changed(self))
        self.options_panel_menu_buttons_edit_field.setShown(False)

        self.options_panel_menu_buttons_edit_confirm = QtGui.QPushButton(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_edit_confirm.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'confirm.png')))
        self.options_panel_menu_buttons_edit_confirm.clicked.connect(lambda:edit_confirm_menu_button(self))
        self.options_panel_menu_buttons_edit_confirm.setShown(False)

        self.options_panel_menu_buttons_edit_cancel = QtGui.QPushButton(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_edit_cancel.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'cancel.png')))
        self.options_panel_menu_buttons_edit_cancel.clicked.connect(lambda:edit_cancel_menu_button(self))
        self.options_panel_menu_buttons_edit_cancel.setShown(False)

        self.options_panel_menu_buttons_position_box = QtGui.QWidget(parent=self.options_panel_menu_panel)

        self.options_panel_menu_buttons_x_position_label = QtGui.QLabel('<small>X POSITION</small>', parent=self.options_panel_menu_buttons_position_box)

        self.options_panel_menu_buttons_x_position = QtGui.QSpinBox(parent=self.options_panel_menu_buttons_position_box)
        self.options_panel_menu_buttons_x_position.editingFinished.connect(lambda:menu_buttons_set_geometry(self))

        self.options_panel_menu_buttons_y_position_label = QtGui.QLabel('<small>Y POSITION</small>', parent=self.options_panel_menu_buttons_position_box)

        self.options_panel_menu_buttons_y_position = QtGui.QSpinBox(parent=self.options_panel_menu_buttons_position_box)
        self.options_panel_menu_buttons_y_position.editingFinished.connect(lambda:menu_buttons_set_geometry(self))

        self.options_panel_menu_buttons_width_label = QtGui.QLabel('<small>WIDTH</small>', parent=self.options_panel_menu_buttons_position_box)

        self.options_panel_menu_buttons_width = QtGui.QSpinBox(parent=self.options_panel_menu_buttons_position_box)
        self.options_panel_menu_buttons_width.editingFinished.connect(lambda:menu_buttons_set_geometry(self))

        self.options_panel_menu_buttons_height_label = QtGui.QLabel('<small>HEIGHT</small>', parent=self.options_panel_menu_buttons_position_box)

        self.options_panel_menu_buttons_height = QtGui.QSpinBox(parent=self.options_panel_menu_buttons_position_box)
        self.options_panel_menu_buttons_height.editingFinished.connect(lambda:menu_buttons_set_geometry(self))

        self.options_panel_menu_buttons_jumpto_label = QtGui.QLabel('JUMP TO', parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_jumpto_label.setGeometry(10,285,360,15)

        self.options_panel_menu_buttons_jumpto = QtGui.QComboBox(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_jumpto.setGeometry(10,300,350,25)
        self.options_panel_menu_buttons_jumpto.activated.connect(lambda:button_jumpto_selected(self))

        self.options_panel_menu_buttons_directions_image = QtGui.QLabel(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_image.setGeometry(155,375,60,60)
        self.options_panel_menu_buttons_directions_image.setPixmap(os.path.join(path_graphics, 'options_panel_menu_positions.png'))

        self.options_panel_menu_buttons_directions_top_label = QtGui.QLabel('TOP DIRECTION', parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_top_label.setGeometry(112,335,145,15)

        self.options_panel_menu_buttons_directions_top = QtGui.QComboBox(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_top.setGeometry(112,350,145,25)
        self.options_panel_menu_buttons_directions_top.activated.connect(lambda:button_directions_selected(self))

        self.options_panel_menu_buttons_directions_right_label = QtGui.QLabel('RIGHT DIRECTION', parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_right_label.setGeometry(215,385,145,15)

        self.options_panel_menu_buttons_directions_right = QtGui.QComboBox(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_right.setGeometry(215,400,145,25)
        self.options_panel_menu_buttons_directions_right.activated.connect(lambda:button_directions_selected(self))

        self.options_panel_menu_buttons_directions_bottom_label = QtGui.QLabel('BOTTOM DIRECTION', parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_bottom_label.setGeometry(112,435,145,15)

        self.options_panel_menu_buttons_directions_bottom = QtGui.QComboBox(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_bottom.setGeometry(112,450,145,25)
        self.options_panel_menu_buttons_directions_bottom.activated.connect(lambda:button_directions_selected(self))

        self.options_panel_menu_buttons_directions_left_label = QtGui.QLabel('LEFT DIRECTION', parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_left_label.setGeometry(10,385,145,15)

        self.options_panel_menu_buttons_directions_left = QtGui.QComboBox(parent=self.options_panel_menu_panel)
        self.options_panel_menu_buttons_directions_left.setGeometry(10,400,145,25)
        self.options_panel_menu_buttons_directions_left.activated.connect(lambda:button_directions_selected(self))

        self.options_panel_video_panel = QtGui.QWidget(parent=self.options_panel)

        self.options_panel_video_intro_video_checkbox = QtGui.QCheckBox('This is the intro video', parent=self.options_panel_video_panel)
        self.options_panel_video_intro_video_checkbox.clicked.connect(lambda:set_intro_video(self))

        self.options_panel_video_reencode_video_checkbox = QtGui.QCheckBox('Reencode this video', parent=self.options_panel_video_panel)
        self.options_panel_video_reencode_video_checkbox.clicked.connect(lambda:set_reencode_video(self))

        self.options_panel_video_resolution_combo = QtGui.QComboBox(parent=self.options_panel_video_panel)
        self.options_panel_video_resolution_combo.activated.connect(lambda:video_resolution_combo_selected(self))

        self.options_panel_video_jumpto_label = QtGui.QLabel('JUMP TO', parent=self.options_panel_video_panel)

        self.options_panel_video_jumpto = QtGui.QComboBox(parent=self.options_panel_video_panel)
        self.options_panel_video_jumpto.activated.connect(lambda:video_jumpto_selected(self))

        self.options_panel_video_chapters_list = QtGui.QListWidget(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_list.clicked.connect(lambda:chapter_selected(self))

        self.options_panel_video_chapters_name_label = QtGui.QLabel('<small>CHAPTER NAME</small>', parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_name_label.setShown(False)

        self.options_panel_video_chapters_name = QtGui.QLineEdit(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_name.textEdited.connect(lambda:check_chapter_name(self))
        self.options_panel_video_chapters_name.setShown(False)

        self.options_panel_video_chapters_timecode_label = QtGui.QLabel('<small>TIMECODE</small>', parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_timecode_label.setShown(False)

        self.options_panel_video_chapters_timecode = QtGui.QLineEdit(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_timecode.textEdited.connect(lambda:check_chapter_name(self))
        self.options_panel_video_chapters_timecode.setShown(False)

        self.options_panel_video_chapters_edit_confirm = QtGui.QPushButton(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_edit_confirm.clicked.connect(lambda:confirm_edit_chapter(self))
        self.options_panel_video_chapters_edit_confirm.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'confirm.png')))
        self.options_panel_video_chapters_edit_confirm.setShown(False)

        self.options_panel_video_chapters_edit_cancel = QtGui.QPushButton(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_edit_cancel.clicked.connect(lambda:hide_edit_chapter(self))
        self.options_panel_video_chapters_edit_cancel.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'cancel.png')))
        self.options_panel_video_chapters_edit_cancel.setShown(False)

        self.options_panel_video_chapters_add = QtGui.QPushButton(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_add.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'add.png')))
        self.options_panel_video_chapters_add.clicked.connect(lambda:add_chapter(self))

        self.options_panel_video_chapters_remove = QtGui.QPushButton(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_remove.clicked.connect(lambda:remove_chapter(self))
        self.options_panel_video_chapters_remove.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'remove.png')))
        self.options_panel_video_chapters_remove.setEnabled(False)

        self.options_panel_video_chapters_edit = QtGui.QPushButton(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_edit.clicked.connect(lambda:edit_chapter(self))
        self.options_panel_video_chapters_edit.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'edit.png')))
        self.options_panel_video_chapters_edit.setEnabled(False)

        self.options_panel_video_chapters_import = QtGui.QPushButton(parent=self.options_panel_video_panel)
        self.options_panel_video_chapters_import.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'import.png')))
        self.options_panel_video_chapters_import.clicked.connect(lambda:import_chapters(self))

        self.nowediting_panel = QtGui.QWidget(parent=self.main_panel)

        self.nowediting_panel_animation = QtCore.QPropertyAnimation(self.nowediting_panel, 'geometry')
        self.nowediting_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.nowediting_dvd_panel = QtGui.QWidget(parent=self.nowediting_panel)
        self.nowediting_dvd_panel_animation = QtCore.QPropertyAnimation(self.nowediting_dvd_panel, 'geometry')
        self.nowediting_dvd_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.nowediting_dvd_panel_background = QtGui.QLabel(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_background.png'))
        self.nowediting_dvd_panel_background.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

        self.nowediting_dvd_panel_project_name_label = QtGui.QLabel(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_project_name_label.setForegroundRole(QtGui.QPalette.Midlight)
        self.nowediting_dvd_panel_project_name_label.setText('PROJECT NAME')

        self.nowediting_dvd_panel_project_name = QtGui.QLineEdit(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_project_name.setGeometry(10,30,470,30)
        self.nowediting_dvd_panel_project_name.editingFinished.connect(lambda:update_changes(self))

        self.nowediting_dvd_panel_new_project_file_button = QtGui.QPushButton(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_new_project_file_button.setGeometry(10, 70, 150, 30)
        self.nowediting_dvd_panel_new_project_file_button.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'new.png')))
        self.nowediting_dvd_panel_new_project_file_button.setText('NEW PROJECT')
        self.nowediting_dvd_panel_new_project_file_button.clicked.connect(lambda:new_project_file(self))

        self.nowediting_dvd_panel_open_project_file_button = QtGui.QPushButton(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_open_project_file_button.setGeometry(170, 70, 150, 30)
        self.nowediting_dvd_panel_open_project_file_button.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'open.png')))
        self.nowediting_dvd_panel_open_project_file_button.setText('OPEN PROJECT')
        self.nowediting_dvd_panel_open_project_file_button.clicked.connect(lambda:open_project_file(self))

        self.nowediting_dvd_panel_save_project_file_button = QtGui.QPushButton(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_save_project_file_button.setGeometry(330, 70, 150, 30)
        self.nowediting_dvd_panel_save_project_file_button.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'save.png')))
        self.nowediting_dvd_panel_save_project_file_button.setText('SAVE PROJECT')
        self.nowediting_dvd_panel_save_project_file_button.clicked.connect(lambda:save_project_file(self))

        self.nowediting_dvd_panel_video_format_label = QtGui.QLabel(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_video_format_label.setGeometry(490,10,145,20)
        self.nowediting_dvd_panel_video_format_label.setForegroundRole(QtGui.QPalette.Midlight)
        self.nowediting_dvd_panel_video_format_label.setText('VIDEO FORMAT')

        class nowediting_dvd_panel_video_format(QtGui.QWidget):
            def mousePressEvent(widget, event):
                nowediting_dvd_panel_video_format_changed(self)

        self.nowediting_dvd_panel_video_format = nowediting_dvd_panel_video_format(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_video_format.setGeometry(490, 30, 145, 25)

        self.nowediting_dvd_panel_video_format_background = QtGui.QLabel(parent=self.nowediting_dvd_panel_video_format)
        self.nowediting_dvd_panel_video_format_background.setGeometry(0,0,self.nowediting_dvd_panel_video_format.width(),self.nowediting_dvd_panel_video_format.height())

        self.nowediting_dvd_panel_audio_format_label = QtGui.QLabel(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_audio_format_label.setGeometry(490,60,145,20)
        self.nowediting_dvd_panel_audio_format_label.setForegroundRole(QtGui.QPalette.Midlight)
        self.nowediting_dvd_panel_audio_format_label.setText('AUDIO FORMAT')

        class nowediting_dvd_panel_audio_format(QtGui.QWidget):
            def mousePressEvent(widget, event):
                nowediting_dvd_panel_audio_format_changed(self)

        self.nowediting_dvd_panel_audio_format = nowediting_dvd_panel_audio_format(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_audio_format.setGeometry(490, 80, 145, 25)

        self.nowediting_dvd_panel_audio_format_background = QtGui.QLabel(parent=self.nowediting_dvd_panel_audio_format)
        self.nowediting_dvd_panel_audio_format_background.setGeometry(0,0,self.nowediting_dvd_panel_audio_format.width(),self.nowediting_dvd_panel_audio_format.height())

        self.nowediting_dvd_panel_aspect_ratio_label = QtGui.QLabel(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_aspect_ratio_label.setGeometry(645,10,100,20)
        self.nowediting_dvd_panel_aspect_ratio_label.setForegroundRole(QtGui.QPalette.Midlight)
        self.nowediting_dvd_panel_aspect_ratio_label.setText('ASPECT RATIO')

        class nowediting_dvd_panel_aspect_ratio(QtGui.QWidget):
            def mousePressEvent(widget, event):
                nowediting_dvd_panel_aspect_ratio_changed(self)

        self.nowediting_dvd_panel_aspect_ratio = nowediting_dvd_panel_aspect_ratio(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_aspect_ratio.setGeometry(645, 30, 100, 61)

        self.nowediting_dvd_panel_aspect_ratio_background = QtGui.QLabel(parent=self.nowediting_dvd_panel_aspect_ratio)
        self.nowediting_dvd_panel_aspect_ratio_background.setGeometry(0,0,self.nowediting_dvd_panel_aspect_ratio.width(),self.nowediting_dvd_panel_aspect_ratio.height())

        self.nowediting_dvd_panel_has_menus_label = QtGui.QLabel(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_has_menus_label.setGeometry(755,10,145,20)
        self.nowediting_dvd_panel_has_menus_label.setForegroundRole(QtGui.QPalette.Midlight)
        self.nowediting_dvd_panel_has_menus_label.setText('USE MENUS')

        class nowediting_dvd_panel_has_menus(QtGui.QWidget):
            def mousePressEvent(widget, event):
                nowediting_dvd_panel_has_menus_changed(self)

        self.nowediting_dvd_panel_has_menus = nowediting_dvd_panel_has_menus(parent=self.nowediting_dvd_panel)
        self.nowediting_dvd_panel_has_menus.setGeometry(755, 30, 145, 25)

        self.nowediting_dvd_panel_has_menus_background = QtGui.QLabel(parent=self.nowediting_dvd_panel_has_menus)
        self.nowediting_dvd_panel_has_menus_background.setGeometry(0,0,self.nowediting_dvd_panel_has_menus.width(),self.nowediting_dvd_panel_has_menus.height())

        self.nowediting_menus_panel = QtGui.QWidget(parent=self.nowediting_panel)
        self.nowediting_menus_panel_animation = QtCore.QPropertyAnimation(self.nowediting_menus_panel, 'geometry')
        self.nowediting_menus_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.nowediting_menus_panel_background = QtGui.QLabel(parent=self.nowediting_menus_panel)
        self.nowediting_menus_panel_background.setPixmap(os.path.join(path_graphics, 'nowediting_menus_panel_background.png'))
        self.nowediting_menus_panel_background.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

        self.nowediting_menus_panel_list = QtGui.QListWidget(parent=self.nowediting_menus_panel)
        self.nowediting_menus_panel_list.setViewMode(QtGui.QListView.IconMode)
        self.nowediting_menus_panel_list.clicked.connect(lambda:menu_selected(self))

        self.nowediting_menus_panel_duplicate = QtGui.QPushButton(parent=self.nowediting_menus_panel)
        self.nowediting_menus_panel_duplicate.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'duplicate.png')))
        self.nowediting_menus_panel_duplicate.clicked.connect(lambda:duplicate_menu(self))
        self.nowediting_menus_panel_duplicate.setEnabled(False)

        self.nowediting_menus_panel_add = QtGui.QPushButton(parent=self.nowediting_menus_panel)
        self.nowediting_menus_panel_add.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'add.png')))
        self.nowediting_menus_panel_add.clicked.connect(lambda:add_menu(self))

        self.nowediting_menus_panel_remove = QtGui.QPushButton(parent=self.nowediting_menus_panel)
        self.nowediting_menus_panel_remove.clicked.connect(lambda:remove_menu(self))
        self.nowediting_menus_panel_remove.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'remove.png')))
        self.nowediting_menus_panel_remove.setEnabled(False)

        self.nowediting_videos_panel = QtGui.QWidget(parent=self.nowediting_panel)
        self.nowediting_videos_panel_animation = QtCore.QPropertyAnimation(self.nowediting_videos_panel, 'geometry')
        self.nowediting_videos_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.nowediting_videos_panel_background = QtGui.QLabel(parent=self.nowediting_videos_panel)
        self.nowediting_videos_panel_background.setPixmap(os.path.join(path_graphics, 'nowediting_videos_panel_background.png'))
        self.nowediting_videos_panel_background.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

        self.nowediting_videos_panel_list = QtGui.QListWidget(parent=self.nowediting_videos_panel)
        self.nowediting_videos_panel_list.setViewMode(QtGui.QListView.IconMode)
        self.nowediting_videos_panel_list.clicked.connect(lambda:video_selected(self))

        self.nowediting_videos_panel_add = QtGui.QPushButton(parent=self.nowediting_videos_panel)
        self.nowediting_videos_panel_add.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'add.png')))
        self.nowediting_videos_panel_add.clicked.connect(lambda:add_video(self))

        self.nowediting_videos_panel_remove = QtGui.QPushButton(parent=self.nowediting_videos_panel)
        self.nowediting_videos_panel_remove.clicked.connect(lambda:remove_video(self))
        self.nowediting_videos_panel_remove.setIcon(QtGui.QPixmap(os.path.join(path_graphics, 'remove.png')))
        self.nowediting_videos_panel_remove.setEnabled(False)

        self.top_panel = QtGui.QWidget(parent=self.main_panel)

        self.top_panel_background = QtGui.QLabel(parent=self.top_panel)
        self.top_panel_background.setPixmap(os.path.join(path_graphics, 'top_panel_background.png'))
        self.top_panel_background.setScaledContents(True)

        self.top_panel_project_name_label = QtGui.QLabel(parent=self.main_panel)
        self.top_panel_project_name_label.setAlignment(QtCore.Qt.AlignVCenter)
        self.top_panel_project_name_label.setForegroundRole(QtGui.QPalette.Light)

        class nowediting_panel_dvd_button(QtGui.QWidget):
            def mousePressEvent(widget, event):
                nowediting_panel_button_changed(self, 'dvd')

        self.nowediting_panel_dvd_button = nowediting_panel_dvd_button(parent=self.nowediting_panel)
        self.nowediting_panel_dvd_button.setGeometry(0,120,116,50)

        self.nowediting_panel_dvd_button_background = QtGui.QLabel(parent=self.nowediting_panel_dvd_button)
        self.nowediting_panel_dvd_button_background.setGeometry(0,0,self.nowediting_panel_dvd_button.width(),self.nowediting_panel_dvd_button.height())
        self.nowediting_panel_dvd_button_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_button_background.png'))

        class nowediting_panel_menus_button(QtGui.QWidget):
            def mousePressEvent(widget, event):
                nowediting_panel_button_changed(self, 'menus')

        self.nowediting_panel_menus_button = nowediting_panel_menus_button(parent=self.nowediting_panel)
        self.nowediting_panel_menus_button.setGeometry(116,120,140,50)

        self.nowediting_panel_menus_button_background = QtGui.QLabel(parent=self.nowediting_panel_menus_button)
        self.nowediting_panel_menus_button_background.setGeometry(0,0,self.nowediting_panel_menus_button.width(),self.nowediting_panel_menus_button.height())
        self.nowediting_panel_menus_button_background.setPixmap(os.path.join(path_graphics, 'nowediting_menus_button_background.png'))

        class nowediting_panel_videos_button(QtGui.QWidget):
            def mousePressEvent(widget, event):
                nowediting_panel_button_changed(self, 'videos')

        self.nowediting_panel_videos_button = nowediting_panel_videos_button(parent=self.nowediting_panel)
        self.nowediting_panel_videos_button.setGeometry(256,120,140,50)

        self.nowediting_panel_videos_button_background = QtGui.QLabel(parent=self.nowediting_panel_videos_button)
        self.nowediting_panel_videos_button_background.setGeometry(0,0,self.nowediting_panel_videos_button.width(),self.nowediting_panel_videos_button.height())
        self.nowediting_panel_videos_button_background.setPixmap(os.path.join(path_graphics, 'nowediting_videos_button_background.png'))

        self.videos_player_panel = QtGui.QWidget(parent=self.main_panel)
        self.videos_player_panel_animation = QtCore.QPropertyAnimation(self.videos_player_panel, 'geometry')
        self.videos_player_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        class videos_player_timeline(QtGui.QWidget):
            def paintEvent(widget, paintEvent):
                painter = QtGui.QPainter(widget)
                if self.selected_video:
                    painter.setRenderHint(QtGui.QPainter.Antialiasing)
                    pixmap = QtGui.QPixmap(os.path.join(path_graphics, 'videos_player_timeline_background.png'))
                    painter.drawPixmap(0,0,pixmap)
                    if self.nowediting == 'videos':
                        for chapter in self.dict_of_videos[self.selected_video][1]:
                            text_size = painter.fontMetrics().width(chapter)
                            mark = convert_timecode_to_miliseconds(self.dict_of_videos[self.selected_video][2][chapter]) / ((self.dict_of_videos[self.selected_video][5]*1000)/self.main_panel.width()-380)
                            if chapter == self.selected_video_chapter:
                                painter.setBrush(QtGui.QColor.fromRgb(80,80,80,a=200))
                            else:
                                painter.setBrush(QtGui.QColor.fromRgb(0,0,0,a=200))
                            painter.setPen(QtGui.QColor.fromRgb(255,255,255))
                            polygon = QtGui.QPolygonF()
                            polygon.append(QtCore.QPointF(mark * 1.0, 0.0))
                            polygon.append(QtCore.QPointF(mark * 1.0, 40.0))
                            polygon.append(QtCore.QPointF((mark * 1.0) + text_size + 10, 40.0))
                            polygon.append(QtCore.QPointF((mark * 1.0) + text_size + 10, 30.0))
                            polygon.append(QtCore.QPointF((mark * 1.0) + 5.0, 30.0))
                            polygon.append(QtCore.QPointF(mark * 1.0, 25.0))
                            painter.drawPolygon(polygon)
                            painter.setFont(QtGui.QFont("Ubuntu", 8))
                            rectangle = QtCore.QRectF((mark * 1.0) + 5.0, 30.0, text_size + 10.0,20.0)
                            painter.drawText(rectangle, QtCore.Qt.AlignLeft, chapter)
                    pixmap = QtGui.QPixmap(os.path.join(path_graphics, 'videos_player_timeline_seek.png'))
                    painter.drawPixmap((self.preview_video_obj.currentTime() / ((self.dict_of_videos[self.selected_video][5]*1000)/self.main_panel.width()-380))-10,0,pixmap)
                painter.end()

            def mousePressEvent(widget, event):
                for chapter in self.dict_of_videos[self.selected_video][1]:
                    text_size = QtGui.QFontMetrics(QtGui.QFont("Ubuntu", 8)).width(chapter)
                    mark = convert_timecode_to_miliseconds(self.dict_of_videos[self.selected_video][2][chapter]) / ((self.dict_of_videos[self.selected_video][5]*1000)/self.main_panel.width()-380)

                    if event.pos().y() > 29.0 and event.pos().y() < 41.0 and event.pos().x() > mark and event.pos().x() < (mark + text_size + 10.0):
                        self.selected_video_chapter = chapter
                        chapter_seek_in_timeline(self)
                        break
                    else:
                        self.selected_video_chapter = None
                if self.selected_video_chapter == None:
                    self.preview_video_obj.seek(event.pos().x() * ((self.dict_of_videos[self.selected_video][5]*1000)/self.main_panel.width()-380) )
                update_timeline(self)

            def mouseReleaseEvent(widget, event):
                update_timeline(self)
            def mouseMoveEvent(widget, event):
                self.preview_video_obj.seek(event.pos().x() * ((self.dict_of_videos[self.selected_video][5]*1000)/self.main_panel.width()-380) )
                update_timeline(self)

        self.videos_player_timeline = videos_player_timeline(parent=self.videos_player_panel)

        self.videos_player_controls_panel = QtGui.QWidget(parent=self.videos_player_panel)
        self.videos_player_controls_panel.setGeometry(160,0,500,50)

        self.videos_player_controls_panel_background = QtGui.QLabel(parent=self.videos_player_controls_panel)
        self.videos_player_controls_panel_background.setGeometry(0,0,self.videos_player_controls_panel.width(),self.videos_player_controls_panel.height())
        self.videos_player_controls_panel_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_background.png'))

        class videos_player_controls_panel_frameback(QtGui.QWidget):
            def mousePressEvent(widget, event):
                video_seek_back_frame(self, 1000/29.97)
                self.videos_player_controls_panel_frameback_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameback_press.png'))
            def enterEvent(widget, event):
                self.videos_player_controls_panel_frameback_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameback_over.png'))
            def mouseReleaseEvent(widget, event):
                self.videos_player_controls_panel_frameback_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameback_background.png'))
            def leaveEvent(widget, event):
                self.videos_player_controls_panel_frameback_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameback_background.png'))

        self.videos_player_controls_panel_frameback = videos_player_controls_panel_frameback(parent=self.videos_player_controls_panel)
        self.videos_player_controls_panel_frameback.setGeometry(0,0,73,50)

        self.videos_player_controls_panel_frameback_background = QtGui.QLabel(parent=self.videos_player_controls_panel_frameback)
        self.videos_player_controls_panel_frameback_background.setGeometry(0,0,self.videos_player_controls_panel_frameback.width(),self.videos_player_controls_panel_frameback.height())
        self.videos_player_controls_panel_frameback_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameback_background.png'))

        class videos_player_controls_panel_stop(QtGui.QWidget):
            def mousePressEvent(widget, event):
                video_stop(self)
                self.videos_player_controls_panel_stop_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_stop_press.png'))
                self.videos_player_controls_panel_play_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_play_background.png'))
                self.videos_player_controls_panel_pause_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_pause_background.png'))

            def enterEvent(widget, event):
                self.videos_player_controls_panel_stop_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_stop_over.png'))
            def mouseReleaseEvent(widget, event):
                self.videos_player_controls_panel_stop_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_stop_background.png'))
            def leaveEvent(widget, event):
                self.videos_player_controls_panel_stop_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_stop_background.png'))

        self.videos_player_controls_panel_stop = videos_player_controls_panel_stop(parent=self.videos_player_controls_panel)
        self.videos_player_controls_panel_stop.setGeometry(72,0,48,50)

        self.videos_player_controls_panel_stop_background = QtGui.QLabel(parent=self.videos_player_controls_panel_stop)
        self.videos_player_controls_panel_stop_background.setGeometry(0,0,self.videos_player_controls_panel_stop.width(),self.videos_player_controls_panel_stop.height())
        self.videos_player_controls_panel_stop_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_stop_background.png'))

        class videos_player_controls_panel_play(QtGui.QWidget):
            def mousePressEvent(widget, event):
                if not self.preview_video_obj.state() == Phonon.PausedState:
                    video_play(self)
                    self.videos_player_controls_panel_play_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_play_press.png'))

            def enterEvent(widget, event):
                if not self.preview_video_obj.state() in [Phonon.PausedState, Phonon.PlayingState]:
                    self.videos_player_controls_panel_play_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_play_over.png'))
            def leaveEvent(widget, event):
                if not self.preview_video_obj.state() in [Phonon.PausedState, Phonon.PlayingState]:
                    self.videos_player_controls_panel_play_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_play_background.png'))

        self.videos_player_controls_panel_play = videos_player_controls_panel_play(parent=self.videos_player_controls_panel)
        self.videos_player_controls_panel_play.setGeometry(121,0,48,50)

        self.videos_player_controls_panel_play_background = QtGui.QLabel(parent=self.videos_player_controls_panel_play)
        self.videos_player_controls_panel_play_background.setGeometry(0,0,self.videos_player_controls_panel_play.width(),self.videos_player_controls_panel_play.height())
        self.videos_player_controls_panel_play_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_play_background.png'))

        class videos_player_controls_panel_pause(QtGui.QWidget):
            def mousePressEvent(widget, event):
                if not self.preview_video_obj.state() in [Phonon.PausedState]:
                    video_pause(self)
                else:
                    video_play(self)
            def enterEvent(widget, event):
                if not self.preview_video_obj.state() in [Phonon.PausedState]:
                    self.videos_player_controls_panel_pause_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_pause_over.png'))
            def mouseReleaseEvent(widget, event):
                if not self.preview_video_obj.state() in [Phonon.PausedState]:
                    self.videos_player_controls_panel_pause_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_pause_background.png'))
            def leaveEvent(widget, event):
                if not self.preview_video_obj.state() in [Phonon.PausedState]:
                    self.videos_player_controls_panel_pause_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_pause_background.png'))

        self.videos_player_controls_panel_pause = videos_player_controls_panel_pause(parent=self.videos_player_controls_panel)
        self.videos_player_controls_panel_pause.setGeometry(169,0,48,50)

        self.videos_player_controls_panel_pause_background = QtGui.QLabel(parent=self.videos_player_controls_panel_pause)
        self.videos_player_controls_panel_pause_background.setGeometry(0,0,self.videos_player_controls_panel_pause.width(),self.videos_player_controls_panel_pause.height())
        self.videos_player_controls_panel_pause_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_pause_background.png'))

        class videos_player_controls_panel_mark(QtGui.QWidget):
            def mousePressEvent(widget, event):
                video_add_this_mark_frame(self)
                self.videos_player_controls_panel_mark_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_mark_press.png'))
            def enterEvent(widget, event):
                self.videos_player_controls_panel_mark_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_mark_over.png'))
            def mouseReleaseEvent(widget, event):
                self.videos_player_controls_panel_mark_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_mark_background.png'))
            def leaveEvent(widget, event):
                self.videos_player_controls_panel_mark_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_mark_background.png'))

        self.videos_player_controls_panel_mark = videos_player_controls_panel_mark(parent=self.videos_player_controls_panel)
        self.videos_player_controls_panel_mark.setGeometry(217,0,48,50)

        self.videos_player_controls_panel_mark_background = QtGui.QLabel(parent=self.videos_player_controls_panel_mark)
        self.videos_player_controls_panel_mark_background.setGeometry(0,0,self.videos_player_controls_panel_mark.width(),self.videos_player_controls_panel_mark.height())
        self.videos_player_controls_panel_mark_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_mark_background.png'))

        class videos_player_controls_panel_frameforward(QtGui.QWidget):
            def mousePressEvent(widget, event):
                video_seek_next_frame(self, 1000/29.97)
                self.videos_player_controls_panel_frameforward_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameforward_press.png'))
            def enterEvent(widget, event):
                self.videos_player_controls_panel_frameforward_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameforward_over.png'))
            def mouseReleaseEvent(widget, event):
                self.videos_player_controls_panel_frameforward_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameforward_background.png'))
            def leaveEvent(widget, event):
                self.videos_player_controls_panel_frameforward_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameforward_background.png'))

        self.videos_player_controls_panel_frameforward = videos_player_controls_panel_frameforward(parent=self.videos_player_controls_panel)
        self.videos_player_controls_panel_frameforward.setGeometry(265,0,74,50)

        self.videos_player_controls_panel_frameforward_background = QtGui.QLabel(parent=self.videos_player_controls_panel_frameforward)
        self.videos_player_controls_panel_frameforward_background.setGeometry(0,0,self.videos_player_controls_panel_frameforward.width(),self.videos_player_controls_panel_frameforward.height())
        self.videos_player_controls_panel_frameforward_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_frameforward_background.png'))

        self.videos_player_controls_panel_current_time = QtGui.QLabel(parent=self.videos_player_controls_panel)
        self.videos_player_controls_panel_current_time.setGeometry(344,10,146,30)
        self.videos_player_controls_panel_current_time.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.videos_player_controls_panel_current_time.setStyleSheet('font-family: "Ubuntu Mono"; font-size:22px; color:#9AC3CF')

        self.menus_properties_panel = QtGui.QWidget(parent=self.main_panel)
        self.menus_properties_panel_animation = QtCore.QPropertyAnimation(self.menus_properties_panel, 'geometry')
        self.menus_properties_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.menus_properties_panel_background = QtGui.QLabel(parent=self.menus_properties_panel)
        self.menus_properties_panel_background.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_background.png'))

        self.menus_properties_panel_background_file_label = QtGui.QLabel(parent=self.menus_properties_panel)
        self.menus_properties_panel_background_file_label.setGeometry(10,30,90,20)
        self.menus_properties_panel_background_file_label.setText('BACKGROUND')

        class menus_properties_panel_background_file_preview(QtGui.QWidget):
            def enterEvent(widget, event):
                self.menus_properties_panel_background_file_preview_open_button.setShown(True)
            def leaveEvent(widget, event):
                self.menus_properties_panel_background_file_preview_open_button.setShown(False)

        self.menus_properties_panel_background_file_preview = menus_properties_panel_background_file_preview(parent=self.menus_properties_panel)

        self.menus_properties_panel_background_file_preview_background = QtGui.QLabel(parent=self.menus_properties_panel_background_file_preview)
        self.menus_properties_panel_background_file_preview_background.setScaledContents(True)
        self.menus_properties_panel_background_file_preview_foreground = QtGui.QLabel(parent=self.menus_properties_panel_background_file_preview)
        self.menus_properties_panel_background_file_preview_open_button = QtGui.QPushButton(QtGui.QPixmap(os.path.join(path_graphics, 'open.png')), '', parent=self.menus_properties_panel_background_file_preview)
        self.menus_properties_panel_background_file_preview_open_button.setGeometry(5,15,30,30)
        self.menus_properties_panel_background_file_preview_open_button.setShown(False)
        self.menus_properties_panel_background_file_preview_open_button.clicked.connect(lambda:select_menu_file(self))

        self.menus_properties_panel_overlay_file_label = QtGui.QLabel(parent=self.menus_properties_panel)
        self.menus_properties_panel_overlay_file_label.setGeometry(110,30,90,20)
        self.menus_properties_panel_overlay_file_label.setText('OVERLAY')

        class menus_properties_panel_overlay_file_preview(QtGui.QWidget):
            def enterEvent(widget, event):
                self.menus_properties_panel_overlay_file_preview_open_button.setShown(True)
            def leaveEvent(widget, event):
                self.menus_properties_panel_overlay_file_preview_open_button.setShown(False)

        self.menus_properties_panel_overlay_file_preview = menus_properties_panel_overlay_file_preview(parent=self.menus_properties_panel)

        self.menus_properties_panel_overlay_file_preview_background = QtGui.QLabel(parent=self.menus_properties_panel_overlay_file_preview)
        self.menus_properties_panel_overlay_file_preview_background.setScaledContents(True)
        self.menus_properties_panel_overlay_file_preview_foreground = QtGui.QLabel(parent=self.menus_properties_panel_overlay_file_preview)
        self.menus_properties_panel_overlay_file_preview_open_button = QtGui.QPushButton(QtGui.QPixmap(os.path.join(path_graphics, 'open.png')), '', parent=self.menus_properties_panel_overlay_file_preview)
        self.menus_properties_panel_overlay_file_preview_open_button.setGeometry(5,15,30,30)
        self.menus_properties_panel_overlay_file_preview_open_button.setShown(False)
        self.menus_properties_panel_overlay_file_preview_open_button.clicked.connect(lambda:select_overlay_file(self))

        self.menus_properties_panel_color_label = QtGui.QLabel(parent=self.menus_properties_panel)
        self.menus_properties_panel_color_label.setGeometry(210,30,50,20)
        self.menus_properties_panel_color_label.setText('COLOR')

        self.options_panel_menu_choose_color_button = QtGui.QPushButton(parent=self.menus_properties_panel)
        self.options_panel_menu_choose_color_button.setGeometry(210, 50, 50,50)
        self.options_panel_menu_choose_color_button.clicked.connect(lambda:choose_color(self))

        self.menus_properties_panel_transparency_slider_label = QtGui.QLabel('OPACITY', parent=self.menus_properties_panel)
        self.menus_properties_panel_transparency_slider_label.setGeometry(270,30,100,20)

        self.menus_properties_panel_transparency_slider = QtGui.QDial(parent=self.menus_properties_panel)
        self.menus_properties_panel_transparency_slider.setGeometry(270,50,50,50)
        self.menus_properties_panel_transparency_slider.setMaximum(100)
        self.menus_properties_panel_transparency_slider.setMinimum(0)
        self.menus_properties_panel_transparency_slider.valueChanged.connect(lambda:transparency_slider_changing(self))
        self.menus_properties_panel_transparency_slider.sliderReleased.connect(lambda:transparency_slider_changed(self))

        self.menus_properties_panel_transparency_slider_value = QtGui.QLabel(parent=self.menus_properties_panel)
        self.menus_properties_panel_transparency_slider_value.setAlignment(QtCore.Qt.AlignVCenter)
        self.menus_properties_panel_transparency_slider_value.setGeometry(320,50,50,50)

        self.menus_properties_panel_border_slider_label = QtGui.QLabel('BORDER', parent=self.menus_properties_panel)
        self.menus_properties_panel_border_slider_label.setGeometry(370,30,100,20)

        self.menus_properties_panel_border_slider = QtGui.QDial(parent=self.menus_properties_panel)
        self.menus_properties_panel_border_slider.setGeometry(370,50,50,50)
        self.menus_properties_panel_border_slider.setMaximum(100)
        self.menus_properties_panel_border_slider.setMinimum(0)
        self.menus_properties_panel_border_slider.valueChanged.connect(lambda:border_slider_changing(self))
        self.menus_properties_panel_border_slider.sliderReleased.connect(lambda:border_slider_changed(self))

        self.menus_properties_panel_border_slider_value = QtGui.QLabel(parent=self.menus_properties_panel)
        self.menus_properties_panel_border_slider_value.setAlignment(QtCore.Qt.AlignVCenter)
        self.menus_properties_panel_border_slider_value.setGeometry(420,50,50,50)

        self.menus_properties_panel_sound_box = QtGui.QLabel('SOUND', parent=self.menus_properties_panel)
        self.menus_properties_panel_sound_box.setGeometry(470,30,100,20)

        self.menus_properties_panel_sound_label = QtGui.QLabel(parent=self.menus_properties_panel)
        self.menus_properties_panel_sound_label.setGeometry(470,50,100,30)
        self.menus_properties_panel_sound_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

        self.menus_properties_panel_sound_open_button = QtGui.QPushButton(QtGui.QPixmap(os.path.join(path_graphics, 'open.png')), 'OPEN', parent=self.menus_properties_panel)
        self.menus_properties_panel_sound_open_button.setGeometry(470, 80, 100,20)
        self.menus_properties_panel_sound_open_button.clicked.connect(lambda:select_menu_sound_file(self))

        class menus_properties_panel_overlay_preview(QtGui.QWidget):
            def mousePressEvent(widget, event):
                preview_overlay_clicked(self)

        self.menus_properties_panel_overlay_preview = menus_properties_panel_overlay_preview(parent=self.menus_properties_panel)
        self.menus_properties_panel_overlay_preview.setGeometry(630,30,180,25)

        self.menus_properties_panel_overlay_preview_background = QtGui.QLabel(parent=self.menus_properties_panel_overlay_preview)
        self.menus_properties_panel_overlay_preview_background.setGeometry(0,0,self.menus_properties_panel_overlay_preview.width(),self.menus_properties_panel_overlay_preview.height())

        self.menus_properties_panel_overlay_preview_label = QtGui.QLabel('PREVIEW OVERLAY', parent=self.menus_properties_panel_overlay_preview)
        self.menus_properties_panel_overlay_preview_label.setGeometry(25,0,self.menus_properties_panel_overlay_preview.width()-25,self.menus_properties_panel_overlay_preview.height())
        self.menus_properties_panel_overlay_preview_label.setForegroundRole(QtGui.QPalette.Light)

        class menus_properties_panel_directions_preview(QtGui.QWidget):
            def mousePressEvent(widget, event):
                preview_directions(self)

        self.menus_properties_panel_directions_preview = menus_properties_panel_directions_preview(parent=self.menus_properties_panel)
        self.menus_properties_panel_directions_preview.setGeometry(630,55,180,25)

        self.menus_properties_panel_directions_preview_background = QtGui.QLabel(parent=self.menus_properties_panel_directions_preview)
        self.menus_properties_panel_directions_preview_background.setGeometry(0,0,self.menus_properties_panel_directions_preview.width(),self.menus_properties_panel_directions_preview.height())

        self.menus_properties_panel_directions_preview_label = QtGui.QLabel('PREVIEW DIRECTIONS', parent=self.menus_properties_panel_directions_preview)
        self.menus_properties_panel_directions_preview_label.setGeometry(25,0,self.menus_properties_panel_directions_preview.width()-25,self.menus_properties_panel_directions_preview.height())
        self.menus_properties_panel_directions_preview_label.setForegroundRole(QtGui.QPalette.Light)

        class menus_properties_panel_main_menu_checkbox(QtGui.QWidget):
            def mousePressEvent(widget, event):
                set_main_menu(self)

        self.menus_properties_panel_main_menu_checkbox = menus_properties_panel_main_menu_checkbox(parent=self.menus_properties_panel)
        self.menus_properties_panel_main_menu_checkbox.setGeometry(626,85,78,25)

        self.menus_properties_panel_main_menu_checkbox_background = QtGui.QLabel(parent=self.menus_properties_panel_main_menu_checkbox)
        self.menus_properties_panel_main_menu_checkbox_background.setGeometry(0,0,self.menus_properties_panel_main_menu_checkbox.width(),self.menus_properties_panel_main_menu_checkbox.height())

        self.lock_finalize_panel = QtGui.QWidget(parent=self.main_panel)
        self.lock_finalize_panel_animation = QtCore.QPropertyAnimation(self.lock_finalize_panel, 'geometry')
        self.lock_finalize_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.lock_finalize_panel_background = QtGui.QLabel(parent=self.lock_finalize_panel)
        self.lock_finalize_panel_background.setGeometry(0,0,self.lock_finalize_panel.width(),self.lock_finalize_panel.height())
        self.lock_finalize_panel_background.setPixmap(os.path.join(path_graphics, 'lock_finalize_panel_background.png'))

        self.lock_finalize_dvd_image = QtGui.QLabel(parent=self.lock_finalize_panel)
        self.lock_finalize_dvd_image.setGeometry(150,745,300,300)
        self.lock_finalize_dvd_image.setPixmap(os.path.join(path_graphics, 'finalize_dvd_image.png'))

        self.lock_finalize_panel_progress_bar_label = QtGui.QLabel('PROGRESS', parent=self.lock_finalize_panel)
        self.lock_finalize_panel_progress_bar_label.setGeometry(460, 845, 400, 30)
        self.lock_finalize_panel_progress_bar_label.setForegroundRole(QtGui.QPalette.Light)
        self.lock_finalize_panel_progress_bar_label.setShown(False)

        self.lock_finalize_panel_progress_bar = QtGui.QProgressBar(parent=self.lock_finalize_panel)
        self.lock_finalize_panel_progress_bar.setGeometry(460, 875, 400, 40)

        self.lock_finalize_panel_progress_bar_description = QtGui.QLabel(parent=self.lock_finalize_panel)
        self.lock_finalize_panel_progress_bar_description.setGeometry(460, 915, 400, 30)
        self.lock_finalize_panel_progress_bar_description.setForegroundRole(QtGui.QPalette.Light)
        self.lock_finalize_panel_progress_bar_description.setShown(False)

        self.finalize_panel = QtGui.QWidget(parent=self.main_panel)
        self.finalize_panel_animation = QtCore.QPropertyAnimation(self.finalize_panel, 'geometry')
        self.finalize_panel_animation.setEasingCurve(QtCore.QEasingCurve.OutCirc)

        self.finalize_panel_background = QtGui.QLabel(parent=self.finalize_panel)
        self.finalize_panel_background.setPixmap(os.path.join(path_graphics, 'finalize_panel_background.png'))

        self.finalize_panel_generate_button = QtGui.QPushButton('Generate\nDVD', parent=self.finalize_panel)
        self.finalize_panel_generate_button.clicked.connect(lambda:dvd_generate(self))

        self.finalize_panel_generate_button_iso_checkbox = QtGui.QCheckBox('ISO', parent=self.finalize_panel_generate_button)
        self.finalize_panel_generate_button_iso_checkbox.clicked.connect(lambda:set_generate_dvd_kind(self))

        self.finalize_panel_generate_button_ddp_checkbox = QtGui.QCheckBox('DDP', parent=self.finalize_panel_generate_button)
        self.finalize_panel_generate_button_ddp_checkbox.clicked.connect(lambda:set_generate_dvd_kind(self))

        self.generate_dvd_thread_thread = generate_dvd_thread()
        self.generate_dvd_thread_thread.signal.sig.connect(self.generate_dvd_thread_thread_completed)

        self.setGeometry(0, 0, QtGui.QDesktopWidget().screenGeometry().width(), QtGui.QDesktopWidget().screenGeometry().height())
        self.showMaximized()
        clean_changes(self)

    def generate_dvd_thread_thread_completed(self, data):

        if data.startswith('START'):
            generate_effect(self, self.lock_finalize_panel_animation, 'geometry', 1000, [self.lock_finalize_panel.x(),self.lock_finalize_panel.y(),self.lock_finalize_panel.width(),self.lock_finalize_panel.height()], [0,-490,1200,1300])
            self.finalize_panel_generate_button.setShown(False)
            self.lock_finalize_panel_progress_bar_label.setShown(True)
            self.lock_finalize_panel_progress_bar.setShown(True)
            self.lock_finalize_panel_progress_bar_description.setShown(True)
            self.lock_finalize_panel_progress_bar.setMaximum(int(data.split(',')[2]))
            self.lock_finalize_panel_progress_bar.setValue(0)
            self.lock_finalize_panel_progress_bar_description.setText("PROCESSING INTRO VIDEO")
        elif data.startswith('FINISH'):
            generate_effect(self, self.lock_finalize_panel_animation, 'geometry', 1000, [self.lock_finalize_panel.x(),self.lock_finalize_panel.y(),1200,1300], [0,self.main_panel.height(),1200,1300])
            self.finalize_panel_generate_button.setShown(True)
            self.lock_finalize_panel_progress_bar_label.setShown(False)
            self.lock_finalize_panel_progress_bar.setShown(False)
            self.lock_finalize_panel_progress_bar_description.setShown(False)
        else:
            self.lock_finalize_panel_progress_bar.setValue(int(data.split(',')[1]))
            self.lock_finalize_panel_progress_bar_description.setText(data.split(',')[0])

    def closeEvent(self, event):
        shutil.rmtree(path_tmp, ignore_errors=True)

    def resizeEvent(self, event):
        self.main_panel.setGeometry(0, 0, self.width(), self.height())
        self.top_panel.setGeometry(0,0,self.main_panel.width(),92)
        self.content_panel.setGeometry(0,-40,self.main_panel.width(),self.main_panel.height()+120)
        self.content_panel_background.setGeometry(0,0,self.content_panel.width(), self.content_panel.height())
        self.options_panel.setGeometry(self.main_panel.width()-380,120,380,self.main_panel.height()-80)
        self.options_panel_background.setGeometry(0,0,self.options_panel.width(), self.options_panel.height())
        self.finalize_panel.setGeometry(self.main_panel.width(),0,370,110)
        self.menus_properties_panel.setGeometry(0,self.main_panel.height(),self.main_panel.width(),125)
        self.lock_finalize_panel.setGeometry(0,self.main_panel.height(),self.main_panel.width(),self.main_panel.height())#-370
        self.videos_player_panel.setGeometry(0,self.main_panel.height(),self.main_panel.width()-380,125)
        self.options_panel_dvd_panel.setGeometry(10,0,self.options_panel.width()-10,self.options_panel.height())
        self.options_panel_menu_panel.setGeometry(10,0,self.options_panel.width()-10,self.options_panel.height())
        self.options_panel_menu_buttons_label.setGeometry(10,35,self.options_panel_menu_panel.width()-20,15)
        self.options_panel_menu_buttons.setGeometry(10,50,self.options_panel_menu_panel.width()-80,190)
        self.options_panel_menu_buttons_edit_field.setGeometry(10,245,self.options_panel_menu_panel.width()-90,30)
        self.options_panel_menu_buttons_edit_confirm.setGeometry(self.options_panel_menu_panel.width()-75,245,30,30)
        self.options_panel_menu_buttons_edit_cancel.setGeometry(self.options_panel_menu_panel.width()-40,245,30,30)
        self.options_panel_menu_buttons_position_box.setGeometry(self.options_panel_menu_panel.width()-60,50,50,215)
        self.options_panel_menu_buttons_x_position_label.setGeometry(0,0,self.options_panel_menu_buttons_position_box.width(),15)
        self.options_panel_menu_buttons_x_position_label.setGeometry(0,0,self.options_panel_menu_buttons_position_box.width(),15)
        self.options_panel_menu_buttons_x_position.setGeometry(0, 15, self.options_panel_menu_buttons_position_box.width(), 20)
        self.options_panel_menu_buttons_y_position_label.setGeometry(0,40,self.options_panel_menu_buttons_position_box.width(),15)
        self.options_panel_menu_buttons_y_position.setGeometry(0, 55, self.options_panel_menu_buttons_position_box.width(), 20)
        self.options_panel_menu_buttons_width_label.setGeometry(0,80,self.options_panel_menu_buttons_position_box.width(),15)
        self.options_panel_menu_buttons_width.setGeometry(0, 95, self.options_panel_menu_buttons_position_box.width(), 20)
        self.options_panel_menu_buttons_height_label.setGeometry(0,120,self.options_panel_menu_buttons_position_box.width(),15)
        self.options_panel_menu_buttons_height.setGeometry(0, 135, self.options_panel_menu_buttons_position_box.width(), 20)
        self.options_panel_video_panel.setGeometry(10,50,self.options_panel.width()-10,self.options_panel.height()-50)
        self.options_panel_video_intro_video_checkbox.setGeometry(10,0,self.options_panel_video_panel.width()-20,25)
        self.options_panel_video_reencode_video_checkbox.setGeometry(10,35,self.options_panel_video_panel.width()-20,25)
        self.options_panel_video_resolution_combo.setGeometry(10,70,self.options_panel_video_panel.width()-20,25)
        self.options_panel_video_jumpto_label.setGeometry(10,105,self.options_panel_video_panel.width()-20,15)
        self.options_panel_video_jumpto.setGeometry(10,120,self.options_panel_video_panel.width()-20,25)
        self.options_panel_video_chapters_list.setGeometry(10,155,self.options_panel_video_panel.width()-20,self.options_panel_video_panel.height()-205)
        self.options_panel_video_chapters_name_label.setGeometry(10,self.options_panel_video_panel.height()-55,((self.options_panel_video_panel.width()-90)*.5)-5,15)
        self.options_panel_video_chapters_name.setGeometry(10,self.options_panel_video_panel.height()-40,((self.options_panel_video_panel.width()-90)*.5)-5,30)
        self.options_panel_video_chapters_timecode_label.setGeometry(((self.options_panel_video_panel.width()-90)*.5)+10,self.options_panel_video_panel.height()-55,((self.options_panel_video_panel.width()-90)*.5)-5,15)
        self.options_panel_video_chapters_timecode.setGeometry(((self.options_panel_video_panel.width()-90)*.5)+10,self.options_panel_video_panel.height()-40,((self.options_panel_video_panel.width()-90)*.5)-5,30)
        self.options_panel_video_chapters_edit_confirm.setGeometry(self.options_panel_video_panel.width()-75,self.options_panel_video_panel.height()-40,30,30)
        self.options_panel_video_chapters_edit_cancel.setGeometry(self.options_panel_video_panel.width()-40,self.options_panel_video_panel.height()-40,30,30)
        self.options_panel_video_chapters_add.setGeometry(10,self.options_panel_video_panel.height()-40,30,30)
        self.options_panel_video_chapters_remove.setGeometry(45,self.options_panel_video_panel.height()-40,30,30)
        self.options_panel_video_chapters_edit.setGeometry(80,self.options_panel_video_panel.height()-40,30,30)
        self.options_panel_video_chapters_import.setGeometry(self.options_panel_video_chapters_list.width() - 20,self.options_panel_video_panel.height()-40,30,30)
        print self.nowediting_panel.y()
        self.nowediting_panel.setGeometry(0,-40,self.main_panel.width(),170)
        self.nowediting_dvd_panel.setGeometry(0,-170,self.nowediting_panel.width(),self.nowediting_panel.height())
        self.nowediting_dvd_panel_background.setGeometry(0,0,self.nowediting_dvd_panel.width(),self.nowediting_dvd_panel.height())
        self.nowediting_dvd_panel_project_name_label.setGeometry(10,10,(self.nowediting_dvd_panel.width()*.5)-10,20)
        self.nowediting_menus_panel.setGeometry(0,-170,self.nowediting_panel.width(),self.nowediting_panel.height())
        self.nowediting_menus_panel_background.setGeometry(0,0,self.nowediting_menus_panel.width(),self.nowediting_menus_panel.height())
        self.nowediting_menus_panel_list.setGeometry(10,10,self.nowediting_menus_panel.width()-60,self.nowediting_menus_panel.height()-70)
        self.nowediting_menus_panel_duplicate.setGeometry(self.nowediting_menus_panel.width()-40,10,30,30)
        self.nowediting_menus_panel_add.setGeometry(self.nowediting_menus_panel.width()-40,40,30,30)
        self.nowediting_menus_panel_remove.setGeometry(self.nowediting_menus_panel.width()-40,80,30,30)
        self.nowediting_videos_panel.setGeometry(0,-170,self.nowediting_panel.width(),self.nowediting_panel.height())
        self.nowediting_videos_panel_background.setGeometry(0,0,self.nowediting_videos_panel.width(),self.nowediting_videos_panel.height())
        self.nowediting_videos_panel_list.setGeometry(10,10,self.nowediting_videos_panel.width()-60,self.nowediting_videos_panel.height()-70)
        self.nowediting_videos_panel_add.setGeometry(self.nowediting_videos_panel.width()-40,40,30,30)
        self.nowediting_videos_panel_remove.setGeometry(self.nowediting_videos_panel.width()-40,80,30,30)
        self.top_panel_background.setGeometry(0,0,self.top_panel.width(),self.top_panel.height())
        self.top_panel_project_name_label.setGeometry(20, 0, self.top_panel.width() , 80)
        self.videos_player_timeline.setGeometry(0,25,self.videos_player_panel.width(),100)
        self.menus_properties_panel_background.setGeometry(0,0,self.menus_properties_panel.width(),self.menus_properties_panel.height())
        self.finalize_panel_background.setGeometry(0,0,self.finalize_panel.width(),self.finalize_panel.height())
        self.finalize_panel_generate_button.setGeometry(self.finalize_panel.width() - 220,20,200,50)
        self.finalize_panel_generate_button_iso_checkbox.setGeometry(self.finalize_panel_generate_button.width() - 60, (self.finalize_panel_generate_button.height()/2) - 20, 50, 20)
        self.finalize_panel_generate_button_ddp_checkbox.setGeometry(self.finalize_panel_generate_button.width() - 60, self.finalize_panel_generate_button.height()/2, 50, 20)

###################################################################################################
########################################################################################### PROJETO
###################################################################################################

def nowediting_dvd_panel_aspect_ratio_changed(self):
    if self.selected_aspect_ratio == 0:
        self.selected_aspect_ratio = 1
    else:
        self.selected_aspect_ratio = 0

    change_aspect_ratio(self)
    nowediting_dvd_panel_aspect_ratio_update(self)

def nowediting_dvd_panel_aspect_ratio_update(self):
    if self.selected_aspect_ratio == 0:
        self.nowediting_dvd_panel_aspect_ratio_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_aspect_ratio_16_9.png'))
    else:
        self.nowediting_dvd_panel_aspect_ratio_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_aspect_ratio_4_3.png'))


def nowediting_dvd_panel_video_format_changed(self):
    if self.selected_video_format == 0:
        self.selected_video_format = 1
    else:
        self.selected_video_format = 0

    nowediting_dvd_panel_video_format_update(self)

def nowediting_dvd_panel_video_format_update(self):
    if self.selected_video_format == 0:
        self.resolutions = ['720x576','704x576','352x576','352x288']
        self.nowediting_dvd_panel_video_format_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_video_format_pal.png'))
    else:
        self.resolutions = ['720x480','704x480','352x480','352x240']
        self.nowediting_dvd_panel_video_format_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_video_format_ntsc.png'))
    self.options_panel_video_resolution_combo.clear()
    self.options_panel_video_resolution_combo.addItems(self.resolutions)

def nowediting_dvd_panel_audio_format_changed(self):
    if self.selected_audio_format == 0:
        self.selected_audio_format = 1
    else:
        self.selected_audio_format = 0

    nowediting_dvd_panel_audio_format_update(self)

def nowediting_dvd_panel_audio_format_update(self):
    if self.selected_audio_format == 0:
        self.nowediting_dvd_panel_audio_format_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_audio_format_mp2.png'))
    else:
        self.nowediting_dvd_panel_audio_format_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_audio_format_ac3.png'))


def nowediting_dvd_panel_has_menus_changed(self):
    self.has_menus = not self.has_menus

    nowediting_dvd_panel_has_menus_update(self)

def nowediting_dvd_panel_has_menus_update(self):
    if self.has_menus:
        self.nowediting_dvd_panel_has_menus_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_has_menus_yes.png'))
    else:
        self.nowediting_dvd_panel_has_menus_background.setPixmap(os.path.join(path_graphics, 'nowediting_dvd_panel_has_menus_no.png'))
    self.nowediting_menus_panel.setEnabled(self.has_menus)

def nowediting_panel_button_changed(self, nowediting):
    self.nowediting = nowediting

    if not self.nowediting == 'menus':
        clean_menus_list_selection(self)

    if not self.nowediting == 'videos':
        clean_videos_list_selection(self)

    if self.nowediting_panel.y() == -40:
        generate_effect(self, self.nowediting_panel_animation, 'geometry', 500, [self.nowediting_panel.x(),self.nowediting_panel.y(),self.nowediting_panel.width(),self.nowediting_panel.height()], [0,80,self.main_panel.width(),170])
        generate_effect(self, self.content_panel_animation, 'geometry', 500, [self.content_panel.x(),self.content_panel.y(),self.content_panel.width(),self.content_panel.height()], [0,80,self.content_panel.width(),self.content_panel.height()])
        generate_effect(self, self.options_panel_animation, 'geometry', 500, [self.options_panel.x(),self.options_panel.y(),self.options_panel.width(),self.options_panel.height()], [self.main_panel.width(),self.options_panel.y(),self.options_panel.width(),self.options_panel.height()])

        if self.preview_video_obj.state() in [Phonon.PlayingState]:
            video_pause(self)
        self.preview_video_widget.setShown(False)
        self.preview.setShown(True)

        if not self.videos_player_panel.y() == self.main_panel.height():
            generate_effect(self, self.videos_player_panel_animation, 'geometry', 500, [self.videos_player_panel.x(),self.videos_player_panel.y(),self.videos_player_panel.width(),self.videos_player_panel.height()], [self.videos_player_panel.x(),self.main_panel.height(),self.videos_player_panel.width(),self.videos_player_panel.height()])
        if not self.menus_properties_panel.y() == self.main_panel.height():
            generate_effect(self, self.menus_properties_panel_animation, 'geometry', 500, [self.menus_properties_panel.x(),self.menus_properties_panel.y(),self.menus_properties_panel.width(),self.menus_properties_panel.height()], [self.menus_properties_panel.x(),self.main_panel.height(),self.menus_properties_panel.width(),self.menus_properties_panel.height()])

    elif self.nowediting_panel.y() == 80:
        if (self.nowediting == 'dvd' and not self.nowediting_panel_dvd_button_background.isVisible()) or (self.nowediting == 'menus' and not self.nowediting_panel_menus_button_background.isVisible()) or (self.nowediting == 'videos' and not self.nowediting_panel_videos_button_background.isVisible()):
            generate_effect(self, self.nowediting_panel_animation, 'geometry', 500, [self.nowediting_panel.x(),self.nowediting_panel.y(),self.nowediting_panel.width(),self.nowediting_panel.height()], [0,-40,self.main_panel.width(),170])
            generate_effect(self, self.content_panel_animation, 'geometry', 500, [self.content_panel.x(),self.content_panel.y(),self.content_panel.width(),self.content_panel.height()], [0,-40,self.content_panel.width(),self.content_panel.height()])
            if not self.options_panel.x() == self.main_panel.width() - 380 and (self.nowediting == 'dvd' or (self.nowediting == 'menus' and self.selected_menu) or (self.nowediting == 'videos' and self.selected_video) ):
                generate_effect(self, self.options_panel_animation, 'geometry', 500, [self.options_panel.x(),self.options_panel.y(),self.options_panel.width(),self.options_panel.height()], [self.main_panel.width()-380,self.options_panel.y(),self.options_panel.width(),self.options_panel.height()])

        if self.nowediting == 'dvd':
            self.options_panel_dvd_panel.setShown(True)
            self.options_panel_menu_panel.setShown(False)
            self.options_panel_video_panel.setShown(False)

        elif self.nowediting == 'menus':
            self.options_panel_dvd_panel.setShown(False)
            self.options_panel_menu_panel.setShown(True)
            self.options_panel_video_panel.setShown(False)
            if self.selected_menu:
                if not self.menus_properties_panel.y() == self.main_panel.height() - 125:
                    generate_effect(self, self.menus_properties_panel_animation, 'geometry', 500, [self.menus_properties_panel.x(),self.menus_properties_panel.y(),self.menus_properties_panel.width(),self.menus_properties_panel.height()], [self.menus_properties_panel.x(),self.main_panel.height() - 125,self.menus_properties_panel.width(),self.menus_properties_panel.height()])
                if not self.options_panel.x() == self.main_panel.width() - 380:
                    generate_effect(self, self.options_panel_animation, 'geometry', 500, [self.options_panel.x(),self.options_panel.y(),self.options_panel.width(),self.options_panel.height()], [self.main_panel.width()-380,self.options_panel.y(),self.options_panel.width(),self.options_panel.height()])

        elif self.nowediting == 'videos':
            self.options_panel_dvd_panel.setShown(False)
            self.options_panel_menu_panel.setShown(False)
            self.options_panel_video_panel.setShown(True)
            if self.selected_video:
                self.preview_video_widget.setShown(True)
                self.preview.setShown(False)
                if not self.videos_player_panel.y() == self.main_panel.height() - 125:
                    generate_effect(self, self.videos_player_panel_animation, 'geometry', 500, [self.videos_player_panel.x(),self.videos_player_panel.y(),self.videos_player_panel.width(),self.videos_player_panel.height()], [self.videos_player_panel.x(),self.main_panel.height() - 125,self.videos_player_panel.width(),self.videos_player_panel.height()])
                if not self.options_panel.x() == self.main_panel.width() - 380:
                    generate_effect(self, self.options_panel_animation, 'geometry', 500, [self.options_panel.x(),self.options_panel.y(),self.options_panel.width(),self.options_panel.height()], [self.main_panel.width()-380,self.options_panel.y(),self.options_panel.width(),self.options_panel.height()])

    if self.nowediting == 'dvd':
        self.nowediting_panel_dvd_button_background.setShown(False)
        self.nowediting_panel_menus_button_background.setShown(True)
        self.nowediting_panel_videos_button_background.setShown(True)
        generate_effect(self, self.nowediting_dvd_panel_animation, 'geometry', 500, [self.nowediting_dvd_panel.x(),self.nowediting_dvd_panel.y(),self.nowediting_dvd_panel.width(),self.nowediting_dvd_panel.height()], [self.nowediting_dvd_panel.x(),0,self.nowediting_dvd_panel.width(),self.nowediting_dvd_panel.height()])
        generate_effect(self, self.nowediting_menus_panel_animation, 'geometry', 500, [self.nowediting_menus_panel.x(),self.nowediting_menus_panel.y(),self.nowediting_menus_panel.width(),self.nowediting_menus_panel.height()], [self.nowediting_menus_panel.x(),-170,self.nowediting_menus_panel.width(),self.nowediting_menus_panel.height()])
        generate_effect(self, self.nowediting_videos_panel_animation, 'geometry', 500, [self.nowediting_videos_panel.x(),self.nowediting_videos_panel.y(),self.nowediting_videos_panel.width(),self.nowediting_videos_panel.height()], [self.nowediting_videos_panel.x(),-170,self.nowediting_videos_panel.width(),self.nowediting_videos_panel.height()])
        generate_effect(self, self.videos_player_panel_animation, 'geometry', 500, [self.videos_player_panel.x(),self.videos_player_panel.y(),self.videos_player_panel.width(),self.videos_player_panel.height()], [self.videos_player_panel.x(),self.main_panel.height(),self.videos_player_panel.width(),self.videos_player_panel.height()])
        generate_effect(self, self.menus_properties_panel_animation, 'geometry', 500, [self.menus_properties_panel.x(),self.menus_properties_panel.y(),self.menus_properties_panel.width(),self.menus_properties_panel.height()], [self.menus_properties_panel.x(),self.main_panel.height(),self.menus_properties_panel.width(),self.menus_properties_panel.height()])

    elif self.nowediting == 'menus':
        self.nowediting_panel_dvd_button_background.setShown(True)
        self.nowediting_panel_menus_button_background.setShown(False)
        self.nowediting_panel_videos_button_background.setShown(True)
        generate_effect(self, self.nowediting_dvd_panel_animation, 'geometry', 500, [self.nowediting_dvd_panel.x(),self.nowediting_dvd_panel.y(),self.nowediting_dvd_panel.width(),self.nowediting_dvd_panel.height()], [self.nowediting_dvd_panel.x(),-170,self.nowediting_dvd_panel.width(),self.nowediting_dvd_panel.height()])
        generate_effect(self, self.nowediting_menus_panel_animation, 'geometry', 500, [self.nowediting_menus_panel.x(),self.nowediting_menus_panel.y(),self.nowediting_menus_panel.width(),self.nowediting_menus_panel.height()], [self.nowediting_menus_panel.x(),0,self.nowediting_menus_panel.width(),self.nowediting_menus_panel.height()])
        generate_effect(self, self.nowediting_videos_panel_animation, 'geometry', 500, [self.nowediting_videos_panel.x(),self.nowediting_videos_panel.y(),self.nowediting_videos_panel.width(),self.nowediting_videos_panel.height()], [self.nowediting_videos_panel.x(),-170,self.nowediting_videos_panel.width(),self.nowediting_videos_panel.height()])
        generate_effect(self, self.videos_player_panel_animation, 'geometry', 500, [self.videos_player_panel.x(),self.videos_player_panel.y(),self.videos_player_panel.width(),self.videos_player_panel.height()], [self.videos_player_panel.x(),self.main_panel.height(),self.videos_player_panel.width(),self.videos_player_panel.height()])

    elif self.nowediting == 'videos':
        self.nowediting_panel_dvd_button_background.setShown(True)
        self.nowediting_panel_menus_button_background.setShown(True)
        self.nowediting_panel_videos_button_background.setShown(False)
        generate_effect(self, self.nowediting_dvd_panel_animation, 'geometry', 500, [self.nowediting_dvd_panel.x(),self.nowediting_dvd_panel.y(),self.nowediting_dvd_panel.width(),self.nowediting_dvd_panel.height()], [self.nowediting_dvd_panel.x(),-170,self.nowediting_dvd_panel.width(),self.nowediting_dvd_panel.height()])
        generate_effect(self, self.nowediting_menus_panel_animation, 'geometry', 500, [self.nowediting_menus_panel.x(),self.nowediting_menus_panel.y(),self.nowediting_menus_panel.width(),self.nowediting_menus_panel.height()], [self.nowediting_menus_panel.x(),-170,self.nowediting_menus_panel.width(),self.nowediting_menus_panel.height()])
        generate_effect(self, self.nowediting_videos_panel_animation, 'geometry', 500, [self.nowediting_videos_panel.x(),self.nowediting_videos_panel.y(),self.nowediting_videos_panel.width(),self.nowediting_videos_panel.height()], [self.nowediting_videos_panel.x(),0,self.nowediting_videos_panel.width(),self.nowediting_videos_panel.height()])
        generate_effect(self, self.menus_properties_panel_animation, 'geometry', 500, [self.menus_properties_panel.x(),self.menus_properties_panel.y(),self.menus_properties_panel.width(),self.menus_properties_panel.height()], [self.menus_properties_panel.x(),self.main_panel.height(),self.menus_properties_panel.width(),self.menus_properties_panel.height()])

    update_changes(self)

def clean_changes(self):
    self.actual_project_file = None
    self.project_name = 'Untitled DVD project'

    self.list_of_menus = []
    self.dict_of_menus = {}

    self.list_of_videos = []
    self.dict_of_videos = {}

    self.selected_menu = None
    self.selected_menu_button = None
    self.selected_menu_button_resizing = False
    self.selected_menu_button_directioning = None
    self.selected_menu_button_directions = [None,None,None,None]
    self.selected_menu_button_preview_difference = [0,0]
    self.selected_video = None
    self.selected_video_chapter = None

    self.selected_video_format = 0
    self.selected_aspect_ratio = 0
    self.selected_audio_format = 0
    self.selected_menu_encoding = 'CBR'
    self.selected_menu_twopass = True
    self.selected_menu_bitrate = 7500
    self.selected_menu_max_bitrate = 9000
    self.selected_video_encoding = 'CBR'
    self.selected_video_twopass = True
    self.selected_video_bitrate = 3500
    self.selected_video_max_bitrate = 6000
    self.selected_gop_size = 12
    self.selected_audio_datarate = '384 kb/s'
    self.has_menus = True

    self.overlay_preview = False
    self.directions_preview = False

    nowediting_dvd_panel_video_format_update(self)
    nowediting_dvd_panel_audio_format_update(self)
    nowediting_dvd_panel_aspect_ratio_update(self)
    options_panel_dvd_panel_menu_encoding_update(self)
    options_panel_dvd_panel_video_encoding_update(self)
    options_panel_dvd_panel_menu_twopass_update(self)
    options_panel_dvd_panel_video_twopass_update(self)
    nowediting_dvd_panel_has_menus_update(self)

    self.no_preview_label.setShown(True)
    self.no_preview_label.setText('<font style="font-size:32px;">Select a menu<br>or a video</font>')

    self.options_panel_menu_buttons_position_box.setEnabled(False)

    self.finalize_panel_generate_button_iso_checkbox.setChecked(True)
    self.finalize_panel_generate_button_ddp_checkbox.setChecked(False)

    self.preview_video_widget.setShown(False)

    self.nowediting_dvd_panel_project_name.setText(self.project_name)

    self.nowediting = 'dvd'
    self.nowediting_panel_dvd_button_background.setShown(False)
    nowediting_panel_button_changed(self, self.nowediting)

    self.options_panel_menu_buttons.clear()
    self.options_panel_video_chapters_list.clear()
    change_aspect_ratio(self)
    main_tabs_changed(self)
    update_changes(self)
    self.really_clean_project = True

def open_project_file(self):
    canceled = False
    if not self.really_clean_project:
        save_message = QtGui.QMessageBox()
        save_message.setText("Would you like to save the project?.")
        save_message.setInformativeText("You nave made some changes in your project.")
        save_message.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
        save_message.setDefaultButton(QtGui.QMessageBox.Save)
        ret = save_message.exec_()
        if ret == QtGui.QMessageBox.Save:
            save_project_file(self)
        if ret == QtGui.QMessageBox.Discard or ret == QtGui.QMessageBox.Save:
            clean_changes(self)
        elif ret == QtGui.QMessageBox.Cancel:
            canceled = True

    if not canceled:
        self.actual_project_file = QtGui.QFileDialog.getOpenFileName(self, 'Select the Open DVD Producer project file', path_home, 'Open DVD Producer files (*.odvdp)')[0]#.toUtf8()
        if self.actual_project_file:
            read_project_file(self)

def save_project_file(self):
    if not self.actual_project_file:
        self.actual_project_file = QtGui.QFileDialog.getSaveFileName(self, 'Select a filename to save', path_home, 'Open DVD Producer files (*.odvdp)')[0]

    if self.actual_project_file:
        codecs.open(os.path.join(self.actual_project_file), 'w', 'utf-8').write(write_project_file(self))

    update_changes(self)

    self.really_clean_project = True

def new_project_file(self):
    clean_changes(self)

def get_absolute_path(self, path):
    return os.path.normpath(os.path.join(self.actual_project_file.replace(self.actual_project_file.split('/')[-1].split('\\')[-1], ''), path))

def get_relative_path(self, path):
    final_path = os.path.relpath(path, self.actual_project_file.replace(self.actual_project_file.split('/')[-1].split('\\')[-1], ''))
    return final_path

def get_preview_file(self, path):
    final_path = path
    if not os.path.isfile(path):
        if path.split('.')[-1] in ['mov', 'm4v', 'mpg', 'm2v', 'mp4']:
            final_path = os.path.join(path_graphics, 'file_not_found.mkv')
        else:
            final_path = os.path.join(path_graphics, 'file_not_found.png')
    return final_path

def read_project_file(self):
    project_file_content = codecs.open(os.path.join(self.actual_project_file), 'r', 'utf-8').read()

    self.list_of_menus = []
    self.dict_of_menus = {}

    self.list_of_videos = []
    self.dict_of_videos = {}

    self.selected_menu_encoding = 'CBR'
    self.selected_video_encoding = 'CBR'
    self.selected_menu_twopass = False
    self.selected_video_twopass = False
    self.has_menus = True

    self.project_name = project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('name="')[1].split('"')[0]
    self.selected_aspect_ratio = int(project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('aspect_ratio="')[1].split('"')[0])
    self.selected_video_format = int(project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('video_format="')[1].split('"')[0])
    self.selected_audio_format = int(project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('audio_format="')[1].split('"')[0])
    if 'video_bitrate="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        self.selected_video_bitrate = int(project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('video_bitrate="')[1].split('"')[0])
    if 'video_max_bitrate="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        self.selected_video_max_bitrate = int(project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('video_max_bitrate="')[1].split('"')[0])
    if 'menu_encoding="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        self.selected_menu_encoding = project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('menu_encoding="')[1].split('"')[0]
    if 'menu_twopass="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        if project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('menu_twopass="')[1].split('"')[0] == 'True':
            self.selected_menu_twopass = True
    if 'video_encoding="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        self.selected_video_encoding = project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('video_encoding="')[1].split('"')[0]
    if 'video_twopass="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        if project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('video_twopass="')[1].split('"')[0] == 'True':
            self.selected_video_twopass = True
    if 'menu_bitrate="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        self.selected_menu_bitrate = int(project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('menu_bitrate="')[1].split('"')[0])
    if 'menu_max_bitrate="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        self.selected_menu_max_bitrate = int(project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('menu_max_bitrate="')[1].split('"')[0])
    if 'gop_size="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        self.selected_gop_size = int(project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('gop_size="')[1].split('"')[0])
    if 'audio_datarate="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        self.selected_audio_datarate = project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('audio_datarate="')[1].split('"')[0]
    if 'has_menus="' in project_file_content.split('<dvd ')[1].split('</dvd>')[0]:
        if project_file_content.split('<dvd ')[1].split('</dvd>')[0].split('has_menus="')[1].split('"')[0] == 'False':
            self.has_menus = False

    if '<menu ' in project_file_content.split('<menus>')[1].split('</menus>')[0]:
        for menu_item in project_file_content.split('<menus>')[1].split('</menus>')[0].split('<menu '):
            if '</menu>' in menu_item:
                menu_name = menu_item.split('>')[0].split('name="')[1].split('"')[0]
                self.list_of_menus.append(menu_name)
                menu_list_for_dict = []
                menu_list_for_dict.append(get_absolute_path(self, menu_item.split('>')[0].split('filepath="')[1].split('"')[0]))
                list_of_buttons = []
                dict_of_buttons = {}
                if '<button ' in menu_item.split('</menu>')[0]:
                    for button_item in menu_item.split('</menu>')[0].split('<button '):
                        if '</button>' in button_item:
                            button_name = button_item.split('name="')[1].split('"')[0]
                            list_of_buttons.append(button_name)
                            button_list_for_dict = []
                            button_list_for_dict.append(float(button_item.split('x="')[1].split('"')[0]))
                            button_list_for_dict.append(float(button_item.split('y="')[1].split('"')[0]))
                            button_list_for_dict.append(float(button_item.split('width="')[1].split('"')[0]))
                            button_list_for_dict.append(float(button_item.split('height="')[1].split('"')[0]))
                            if button_item.split('jump_to="')[1].split('"')[0] == 'None':
                                button_list_for_dict.append(None)
                            else:
                                button_list_for_dict.append(button_item.split('jump_to="')[1].split('"')[0])
                            direction_list = []
                            if 'direction_top="' in button_item and not button_item.split('direction_top="')[1].split('"')[0] == 'None':
                                direction_list.append(button_item.split('direction_top="')[1].split('"')[0])
                            else:
                                direction_list.append(None)
                            if 'direction_right="' in button_item and not button_item.split('direction_right="')[1].split('"')[0] == 'None':
                                direction_list.append(button_item.split('direction_right="')[1].split('"')[0])
                            else:
                                direction_list.append(None)
                            if 'direction_bottom="' in button_item and not button_item.split('direction_bottom="')[1].split('"')[0] == 'None':
                                direction_list.append(button_item.split('direction_bottom="')[1].split('"')[0])
                            else:
                                direction_list.append(None)
                            if 'direction_left="' in button_item and not button_item.split('direction_left="')[1].split('"')[0] == 'None':
                                direction_list.append(button_item.split('direction_left="')[1].split('"')[0])
                            else:
                                direction_list.append(None)
                            button_list_for_dict.append(direction_list)
                            dict_of_buttons[button_name] = button_list_for_dict
                menu_list_for_dict.append(list_of_buttons)
                menu_list_for_dict.append(dict_of_buttons)
                if 'overlay="' in menu_item.split('>')[0]:
                    menu_list_for_dict.append(get_absolute_path(self, menu_item.split('>')[0].split('overlay="')[1].split('"')[0]))
                else:
                    menu_list_for_dict.append(None)

                if 'overlay_color="' in menu_item.split('>')[0]:
                    menu_list_for_dict.append(menu_item.split('>')[0].split('overlay_color="')[1].split('"')[0])
                else:
                    menu_list_for_dict.append(None)

                if 'sound="' in menu_item.split('>')[0]:
                    menu_list_for_dict.append(get_absolute_path(self, menu_item.split('>')[0].split('sound="')[1].split('"')[0]))
                else:
                    menu_list_for_dict.append(None)

                if 'main_menu="' in menu_item.split('>')[0] and menu_item.split('>')[0].split('main_menu="')[1].split('"')[0] == 'True':
                    menu_list_for_dict.append(True)
                else:
                    menu_list_for_dict.append(False)

                if 'transparency="' in menu_item.split('>')[0]:
                    menu_list_for_dict.append(float(menu_item.split('>')[0].split('transparency="')[1].split('"')[0]))
                else:
                    menu_list_for_dict.append(.5)

                if 'border="' in menu_item.split('>')[0]:
                    menu_list_for_dict.append(float(menu_item.split('>')[0].split('border="')[1].split('"')[0]))
                else:
                    menu_list_for_dict.append(.5)

                if 'length="' in menu_item.split('>')[0]:
                    menu_list_for_dict.append(float(menu_item.split('>')[0].split('length="')[1].split('"')[0]))
                else:
                    menu_list_for_dict.append(60.0)

                self.dict_of_menus[menu_name] = menu_list_for_dict

    if '<video ' in project_file_content.split('<videos>')[1].split('</videos>')[0]:
        for video_item in project_file_content.split('<videos>')[1].split('</videos>')[0].split('<video'):
            if '</video>' in video_item:
                video_name = video_item.split(' name="')[1].split('"')[0]
                video_path = get_absolute_path(self, video_item.split(' filepath="')[1].split('"')[0])
                list_of_chapters = []
                dict_of_chapters = {}
                is_intro = False
                reencode = False
                post = None
                resolution = 0
                if 'is_intro=' in video_item:
                    if video_item.split(' is_intro="')[1].split('"')[0] == 'True':
                        is_intro = True
                if 'reencode=' in video_item:
                    if video_item.split(' reencode="')[1].split('"')[0] == 'True':
                        reencode = True
                if 'post=' in video_item:
                    if not video_item.split(' post="')[1].split('"')[0] == 'None':
                        post = video_item.split(' post="')[1].split('"')[0]
                if 'resolution=' in video_item:
                    resolution = int(video_item.split(' resolution="')[1].split('"')[0])
                if 'length=' in video_item:
                    length = float(video_item.split(' length="')[1].split('"')[0])
                else:
                    if os.path.isfile(video_path):
                        length_xml = unicode(subprocess.Popen([ffprobe_bin,'-loglevel', 'error',  '-show_format', '-print_format', 'xml', video_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read(), 'utf-8')
                        length = float(length_xml.split(' duration="')[1].split('"')[0])
                    else:
                        length = 60.0
                if '<chapter' in video_item:
                    for chapter_item in video_item.split('<chapter'):
                        if '</chapter>' in chapter_item:
                            chapter_name = chapter_item.split(' name="')[1].split('"')[0]
                            chapter_time = chapter_item.split(' time="')[1].split('"')[0]
                            list_of_chapters.append(chapter_name)
                            dict_of_chapters[chapter_name] = chapter_time
                self.dict_of_videos[video_name] = [video_path, list_of_chapters, dict_of_chapters, is_intro, reencode, length, post, resolution]
                self.list_of_videos.append(video_name)

    self.nowediting_dvd_panel_project_name.setText(self.project_name)

    change_aspect_ratio(self)
    populate_menus_list(self)
    populate_videos_list(self)
    nowediting_dvd_panel_video_format_update(self)
    nowediting_dvd_panel_audio_format_update(self)
    nowediting_dvd_panel_aspect_ratio_update(self)
    options_panel_dvd_panel_menu_encoding_update(self)
    options_panel_dvd_panel_video_encoding_update(self)
    options_panel_dvd_panel_menu_twopass_update(self)
    options_panel_dvd_panel_video_twopass_update(self)
    nowediting_dvd_panel_has_menus_update(self)
    update_changes(self)

    self.really_clean_project = True

def write_project_file(self):
    final_project_file = u'<?xml version="1.0" encoding="UTF-8"?>'
    final_project_file += '<dvd name="' + self.project_name + '"'
    final_project_file += ' aspect_ratio="' + str(self.selected_aspect_ratio)  + '"'
    final_project_file += ' video_format="' + str(self.selected_video_format)  + '"'
    final_project_file += ' audio_format="' + str(self.selected_audio_format)  + '"'
    final_project_file += ' video_encoding="' + str(self.selected_video_encoding)  + '"'
    final_project_file += ' video_bitrate="' + str(self.selected_video_bitrate)  + '"'
    final_project_file += ' video_max_bitrate="' + str(self.selected_video_max_bitrate)  + '"'
    final_project_file += ' menu_encoding="' + str(self.selected_menu_encoding) + '"'
    final_project_file += ' menu_twopass="' + str(self.selected_menu_twopass) + '"'
    final_project_file += ' video_encoding="' + str(self.selected_video_encoding) + '"'
    final_project_file += ' video_twopass="' + str(self.selected_video_twopass) + '"'
    final_project_file += ' menu_bitrate="' + str(self.selected_menu_bitrate) + '"'
    final_project_file += ' menu_max_bitrate="' + str(self.selected_menu_max_bitrate) + '"'
    final_project_file += ' audio_datarate="' + self.selected_audio_datarate + '"'
    final_project_file += ' has_menus="' + str(self.has_menus) + '"'
    final_project_file += ' gop_size="' + str(self.selected_gop_size) + '">'

    final_project_file += '<menus>'
    for menu in self.list_of_menus:
        final_project_file += '<menu name="' + menu + '" filepath="' + get_relative_path(self, self.dict_of_menus[menu][0]) + '"'
        if self.dict_of_menus[menu][3]:
            final_project_file += ' overlay="' + get_relative_path(self, self.dict_of_menus[menu][3]) + '"'
        if self.dict_of_menus[menu][4]:
            final_project_file += ' overlay_color="' + self.dict_of_menus[menu][4] + '"'
        if self.dict_of_menus[menu][5]:
            final_project_file += ' sound="' + get_relative_path(self, self.dict_of_menus[menu][5]) + '"'
        final_project_file += ' main_menu="' + str(self.dict_of_menus[menu][6]) + '"'
        final_project_file += ' transparency="' + str(self.dict_of_menus[menu][7]) + '"'
        final_project_file += ' border="' + str(self.dict_of_menus[menu][8]) + '"'
        final_project_file += ' length="' + str(self.dict_of_menus[menu][9]) + '"'
        final_project_file += '>'
        for button in self.dict_of_menus[menu][1]:
            final_project_file += '<button name="' + button + '" x="' + str(self.dict_of_menus[menu][2][button][0]) + '" y="' + str(self.dict_of_menus[menu][2][button][1]) + '" width="' + str(self.dict_of_menus[menu][2][button][2]) + '" height="' + str(self.dict_of_menus[menu][2][button][3]) + '" jump_to="' + str(self.dict_of_menus[menu][2][button][4])+ '" direction_top="' + str(self.dict_of_menus[menu][2][button][5][0]) + '" direction_right="' + str(self.dict_of_menus[menu][2][button][5][1]) + '" direction_bottom="' + str(self.dict_of_menus[menu][2][button][5][2]) + '" direction_left="' + str(self.dict_of_menus[menu][2][button][5][3]) + '"></button>'
        final_project_file += '</menu>'
    final_project_file += '</menus>'
    final_project_file += '<videos>'
    for video in self.list_of_videos:
        final_project_file += '<video name="' + video + '"'
        final_project_file += ' filepath="' + get_relative_path(self, self.dict_of_videos[video][0]) + '"'
        final_project_file += ' reencode="' + str(self.dict_of_videos[video][4]) + '"'
        final_project_file += ' length="' + str(self.dict_of_videos[video][5]) + '"'
        final_project_file += ' is_intro="' + str(self.dict_of_videos[video][3]) + '"'
        final_project_file += ' post="' + str(self.dict_of_videos[video][6]) + '"'
        final_project_file += ' resolution="' + str(self.dict_of_videos[video][7]) + '">'
        for chapter in self.dict_of_videos[video][1]:
            final_project_file += '<chapter name="' + str(chapter) + '"'
            final_project_file += ' time="' + self.dict_of_videos[video][2][chapter] + '">'
            final_project_file += '</chapter>'
        final_project_file += '</video>'
    final_project_file += '</videos>'
    final_project_file += '</dvd>'

    return final_project_file

def options_panel_dvd_panel_bitrates_changed(self):
    self.selected_menu_bitrate = self.options_panel_dvd_panel_menu_bitrate_field.value()
    self.selected_menu_max_bitrate = self.options_panel_dvd_panel_menu_max_bitrate_field.value()
    self.selected_video_bitrate = self.options_panel_dvd_panel_video_bitrate_field.value()
    self.selected_video_max_bitrate = self.options_panel_dvd_panel_video_max_bitrate_field.value()
    update_changes(self)

def options_panel_dvd_panel_gop_changed(self):
    self.really_clean_project = False
    self.selected_gop_size = int(self.options_panel_dvd_panel_gop.currentText())
    update_changes(self)

def options_panel_dvd_panel_audio_datarate_changed(self):
    self.really_clean_project = False
    self.selected_audio_datarate = self.options_panel_dvd_panel_audio_datarate.currentText()
    update_changes(self)

def options_panel_dvd_panel_menu_encoding_changed(self):
    if self.selected_menu_encoding == 'CBR':
        self.selected_menu_encoding = 'VBR'
    else:
        self.selected_menu_encoding = 'CBR'
    options_panel_dvd_panel_menu_encoding_update(self)

def options_panel_dvd_panel_menu_encoding_update(self):
    if self.selected_menu_encoding == 'CBR':
        self.options_panel_dvd_panel_menu_encoding_background.setPixmap(os.path.join(path_graphics, 'options_panel_dvd_encoding_cbr.png'))
        self.options_panel_dvd_panel_menu_twopass_label.setShown(False)
        self.options_panel_dvd_panel_menu_twopass.setShown(False)
        self.options_panel_dvd_panel_menu_max_bitrate_label.setShown(False)
        self.options_panel_dvd_panel_menu_max_bitrate_field.setShown(False)
        self.options_panel_dvd_panel_menu_max_bitrate_field_label.setShown(False)
    else:
        self.options_panel_dvd_panel_menu_encoding_background.setPixmap(os.path.join(path_graphics, 'options_panel_dvd_encoding_vbr.png'))
        self.options_panel_dvd_panel_menu_twopass_label.setShown(True)
        self.options_panel_dvd_panel_menu_twopass.setShown(True)
        self.options_panel_dvd_panel_menu_max_bitrate_label.setShown(True)
        self.options_panel_dvd_panel_menu_max_bitrate_field.setShown(True)
        self.options_panel_dvd_panel_menu_max_bitrate_field_label.setShown(True)

def options_panel_dvd_panel_video_encoding_changed(self):
    if self.selected_video_encoding == 'CBR':
        self.selected_video_encoding = 'VBR'
    else:
        self.selected_video_encoding = 'CBR'
    options_panel_dvd_panel_video_encoding_update(self)

def options_panel_dvd_panel_video_encoding_update(self):
    if self.selected_video_encoding == 'CBR':
        self.options_panel_dvd_panel_video_encoding_background.setPixmap(os.path.join(path_graphics, 'options_panel_dvd_encoding_cbr.png'))
        self.options_panel_dvd_panel_video_twopass_label.setShown(False)
        self.options_panel_dvd_panel_video_twopass.setShown(False)
        self.options_panel_dvd_panel_video_max_bitrate_label.setShown(False)
        self.options_panel_dvd_panel_video_max_bitrate_field.setShown(False)
        self.options_panel_dvd_panel_video_max_bitrate_field_label.setShown(False)
    else:
        self.options_panel_dvd_panel_video_encoding_background.setPixmap(os.path.join(path_graphics, 'options_panel_dvd_encoding_vbr.png'))
        self.options_panel_dvd_panel_video_twopass_label.setShown(True)
        self.options_panel_dvd_panel_video_twopass.setShown(True)
        self.options_panel_dvd_panel_video_max_bitrate_label.setShown(True)
        self.options_panel_dvd_panel_video_max_bitrate_field.setShown(True)
        self.options_panel_dvd_panel_video_max_bitrate_field_label.setShown(True)

def options_panel_dvd_panel_menu_twopass_changed(self):
    self.selected_menu_twopass = not self.selected_menu_twopass
    options_panel_dvd_panel_menu_twopass_update(self)

def options_panel_dvd_panel_menu_twopass_update(self):
    if self.selected_menu_twopass:
        self.options_panel_dvd_panel_menu_twopass_background.setPixmap(os.path.join(path_graphics, 'options_panel_dvd_passes_two.png'))
    else:
        self.options_panel_dvd_panel_menu_twopass_background.setPixmap(os.path.join(path_graphics, 'options_panel_dvd_passes_one.png'))

def options_panel_dvd_panel_video_twopass_changed(self):
    self.selected_video_twopass = not self.selected_video_twopass
    options_panel_dvd_panel_video_twopass_update(self)

def options_panel_dvd_panel_video_twopass_update(self):
    if self.selected_video_twopass:
        self.options_panel_dvd_panel_video_twopass_background.setPixmap(os.path.join(path_graphics, 'options_panel_dvd_passes_two.png'))
    else:
        self.options_panel_dvd_panel_video_twopass_background.setPixmap(os.path.join(path_graphics, 'options_panel_dvd_passes_one.png'))

def update_changes(self):
    if self.options_panel_menu_buttons_edit_field.isVisible():
        edit_cancel_menu_button(self)

    self.project_name = self.nowediting_dvd_panel_project_name.text()

    if self.actual_project_file:
            self.top_panel_project_name_label.setText('<font style="font-size:18px; font-weight:200;">' + self.project_name + '</font><br><font style="font-size:14px;">' + self.actual_project_file + '</font>')
    else:
        self.top_panel_project_name_label.setText('<font style="font-size:18px; font-weight:200;">' + self.project_name + '</font><br><font style="font-size:14px;">Not saved</font>')

    if self.selected_menu:
        self.no_preview_label.setShown(False)

        self.menus_properties_panel_transparency_slider_value.setText(str(int(self.dict_of_menus[self.selected_menu][7]*100)) + '%')
        self.menus_properties_panel_border_slider_value.setText(str(int(self.dict_of_menus[self.selected_menu][8]*100)) + '%')

        self.menus_properties_panel_transparency_slider.setValue(int(self.dict_of_menus[self.selected_menu][7]*100))
        self.menus_properties_panel_border_slider.setValue(int(self.dict_of_menus[self.selected_menu][8]*100))

        self.menus_properties_panel_background_file_preview_background.setPixmap(os.path.join(path_tmp, self.selected_menu + '.preview.png'))

        if self.dict_of_menus[self.selected_menu][3]:
            self.menus_properties_panel_overlay_file_preview_background.setPixmap(self.dict_of_menus[self.selected_menu][3])
        else:
            self.menus_properties_panel_overlay_file_preview_background.setPixmap(None)

        if self.dict_of_menus[self.selected_menu][4]:
            self.options_panel_menu_choose_color_button.setStyleSheet('background-color:' + self.dict_of_menus[self.selected_menu][4])
        else:
            self.options_panel_menu_choose_color_button.setStyleSheet('background-color:white')

        if self.dict_of_menus[self.selected_menu][0].split('.')[-1] == 'png':
            self.menus_properties_panel_sound_box.setShown(True)
            self.menus_properties_panel_sound_label.setShown(True)
            self.menus_properties_panel_sound_open_button.setShown(True)

            if self.dict_of_menus[self.selected_menu][5]:
                self.menus_properties_panel_sound_label.setText('<small>' + self.dict_of_menus[self.selected_menu][5].split('/')[-1].split('\\')[-1] + '</small>')
            else:
                self.menus_properties_panel_sound_label.setText('<small>' + 'No selected audio' + '</small>')
        else:
            self.menus_properties_panel_sound_box.setShown(False)
            self.menus_properties_panel_sound_label.setShown(False)
            self.menus_properties_panel_sound_open_button.setShown(False)

        if self.dict_of_menus[self.selected_menu][6]:
            self.menus_properties_panel_main_menu_checkbox_background.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_main_menu_checkbox_checked.png'))
        else:
            self.menus_properties_panel_main_menu_checkbox_background.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_main_menu_checkbox_unchecked.png'))

        if self.overlay_preview:
            self.menus_properties_panel_overlay_preview_background.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_preview_checked.png'))
        else:
            self.menus_properties_panel_overlay_preview_background.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_preview_unchecked.png'))

        if self.directions_preview:
            self.menus_properties_panel_directions_preview_background.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_preview_checked.png'))
        else:
            self.menus_properties_panel_directions_preview_background.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_preview_unchecked.png'))

        if self.selected_menu_button:
            self.options_panel_menu_buttons_x_position.setValue(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][0])
            self.options_panel_menu_buttons_y_position.setValue(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][1])
            self.options_panel_menu_buttons_width.setValue(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][2])
            self.options_panel_menu_buttons_height.setValue(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][3])

            populate_jumpto(self)

            if self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][4]:
                self.options_panel_menu_buttons_jumpto.setCurrentIndex(self.options_panel_menu_buttons_jumpto.findText(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][4]))
            else:
                self.options_panel_menu_buttons_jumpto.setCurrentIndex(-1)

            populate_button_directions_list(self)

            if self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][0]:
                self.options_panel_menu_buttons_directions_top.setCurrentIndex(self.options_panel_menu_buttons_directions_top.findText(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][0]))
            else:
                self.options_panel_menu_buttons_directions_top.setCurrentIndex(0)

            if self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][1]:
                self.options_panel_menu_buttons_directions_right.setCurrentIndex(self.options_panel_menu_buttons_directions_right.findText(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][1]))
            else:
                self.options_panel_menu_buttons_directions_right.setCurrentIndex(0)

            if self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][2]:
                self.options_panel_menu_buttons_directions_bottom.setCurrentIndex(self.options_panel_menu_buttons_directions_bottom.findText(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][2]))
            else:
                self.options_panel_menu_buttons_directions_bottom.setCurrentIndex(0)

            if self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][3]:
                self.options_panel_menu_buttons_directions_left.setCurrentIndex(self.options_panel_menu_buttons_directions_left.findText(self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5][3]))
            else:
                self.options_panel_menu_buttons_directions_left.setCurrentIndex(0)

        if self.nowediting == 'menus' and not self.nowediting_panel.y() == -40: #self.menus_properties_panel.y() == self.main_panel.height() and
            generate_effect(self, self.menus_properties_panel_animation, 'geometry', 500, [self.menus_properties_panel.x(),self.menus_properties_panel.y(),self.menus_properties_panel.width(),self.menus_properties_panel.height()], [self.menus_properties_panel.x(),self.main_panel.height()-125,self.menus_properties_panel.width(),self.menus_properties_panel.height()])
            generate_effect(self, self.options_panel_animation, 'geometry', 500, [self.options_panel.x(),self.options_panel.y(),self.options_panel.width(),self.options_panel.height()], [self.main_panel.width()-380,self.options_panel.y(),self.options_panel.width(),self.options_panel.height()])
        elif self.nowediting == 'menus' and self.nowediting_panel.y() == 80:
            generate_effect(self, self.menus_properties_panel_animation, 'geometry', 500, [self.menus_properties_panel.x(),self.menus_properties_panel.y(),self.menus_properties_panel.width(),self.menus_properties_panel.height()], [self.menus_properties_panel.x(),self.main_panel.height(),self.menus_properties_panel.width(),self.menus_properties_panel.height()])

        if len(self.list_of_menus) == 1:
            self.menus_properties_panel_main_menu_checkbox.setShown(False)
        else:
            self.menus_properties_panel_main_menu_checkbox.setShown(True)

    if self.selected_video:
        populate_chapters_list(self)
        if not self.selected_video_chapter:
            self.options_panel_video_chapters_remove.setEnabled(False)
            self.options_panel_video_chapters_edit.setEnabled(False)

        if self.nowediting == 'videos' and self.videos_player_panel.y() == self.main_panel.height():
            generate_effect(self, self.videos_player_panel_animation, 'geometry', 500, [self.videos_player_panel.x(),self.videos_player_panel.y(),self.videos_player_panel.width(),self.videos_player_panel.height()], [self.videos_player_panel.x(),self.main_panel.height()-125,self.videos_player_panel.width(),self.videos_player_panel.height()])
        populate_jumpto_list(self)
        if self.dict_of_videos[self.selected_video][6]:
            self.options_panel_video_jumpto.setCurrentIndex(self.options_panel_video_jumpto.findText(self.dict_of_videos[self.selected_video][6]))
        else:
            self.options_panel_video_jumpto.setCurrentIndex(self.options_panel_video_jumpto.findText('Main menu'))

        self.options_panel_video_intro_video_checkbox.setChecked(self.dict_of_videos[self.selected_video][3])
        self.options_panel_video_reencode_video_checkbox.setChecked(self.dict_of_videos[self.selected_video][4])
        self.options_panel_video_resolution_combo.setEnabled(self.dict_of_videos[self.selected_video][4])
        self.options_panel_video_resolution_combo.setCurrentIndex(self.dict_of_videos[self.selected_video][7])

    if ((not self.has_menus) or (self.has_menus and len(self.list_of_menus) > 0)) and len(self.list_of_videos) > 0:
        generate_effect(self, self.finalize_panel_animation, 'geometry', 500, [self.finalize_panel.x(),self.finalize_panel.y(),self.finalize_panel.width(),self.finalize_panel.height()], [self.main_panel.width() - 370,self.finalize_panel.y(),self.finalize_panel.width(),self.finalize_panel.height()])
    else:
        generate_effect(self, self.finalize_panel_animation, 'geometry', 500, [self.finalize_panel.x(),self.finalize_panel.y(),self.finalize_panel.width(),self.finalize_panel.height()], [self.main_panel.width(),self.finalize_panel.y(),self.finalize_panel.width(),self.finalize_panel.height()])

    self.options_panel_dvd_panel_dvd_image.update()

    estimated_size = 0.0
    estimated_proportion = 0

    if len(self.list_of_videos) > 0:
        if self.has_menus and len(self.list_of_menus) > 0:
            for menu in self.list_of_menus:
                estimated_size += float(((self.selected_menu_bitrate + int(self.selected_audio_datarate.split(' ')[0]))*.001) * self.dict_of_menus[menu][9])
        for video in self.list_of_videos:
            estimated_size += float(((self.selected_video_bitrate + int(self.selected_audio_datarate.split(' ')[0]))*.001) * self.dict_of_videos[video][5])
        estimated_proportion = int(estimated_size / 360)

    final_text = '<font style="font-size:12px;"><b>ESTIMATED SIZE:</b></font><br><font style="font-size:18px;"><b>'
    if estimated_size*.000125 < 1.0:
        final_text += str("%.2f" % round(estimated_size*.125,2)) + ' MB'
    else:
        final_text += str("%.2f" % round(estimated_size/8590.0,2)) + ' GB'
    final_text += ' (' + str(estimated_proportion) + '%)</b></font>'

    self.options_panel_dvd_panel_size_info.setText(final_text)

    self.options_panel_dvd_panel_menu_bitrate_field.setValue(self.selected_menu_bitrate)
    self.options_panel_dvd_panel_menu_max_bitrate_field.setValue(self.selected_menu_max_bitrate)
    self.options_panel_dvd_panel_video_bitrate_field.setValue(self.selected_video_bitrate)
    self.options_panel_dvd_panel_video_max_bitrate_field.setValue(self.selected_video_max_bitrate)
    self.options_panel_dvd_panel_gop.setCurrentIndex(self.options_panel_dvd_panel_gop.findText(str(self.selected_gop_size)))
    self.options_panel_dvd_panel_audio_datarate.setCurrentIndex(self.options_panel_dvd_panel_audio_datarate.findText(self.selected_audio_datarate))

    self.preview.update()

def main_tabs_changed(self):
    if self.nowediting == 'menus':
        self.options_panel_menu_panel_0.setShown(False)
        self.options_panel_menu_buttons_panel_0.setShown(False)
        self.options_panel_video_panel.setShown(True)
        self.options_panel_video_chapters_panel_0.setShown(True)
        self.preview_video_widget.setShown(False)
        self.preview_video_play_button.setShown(False)
        self.preview_video_pause_button.setShown(False)
        self.preview_video_stop_button.setShown(False)
        self.preview_video_seek_back_frame_button.setShown(False)
        self.preview_video_seek_next_frame_button.setShown(False)
        self.preview_video_add_this_mark_button.setShown(False)
        self.menus_properties_panel_overlay_preview_button.setShown(True)
        #if not self.selected_menu:
        clean_menus_list_selection(self)
        self.selected_video = None
    elif self.nowediting == 'videos':
        self.options_panel_menu_panel_0.setShown(True)
        self.options_panel_menu_buttons_panel_0.setShown(True)
        self.options_panel_video_panel.setShown(False)
        self.options_panel_video_chapters_panel_0.setShown(False)
        self.preview_video_play_button.setShown(True)
        self.preview_video_pause_button.setShown(True)
        self.preview_video_stop_button.setShown(True)
        self.preview_video_seek_back_frame_button.setShown(True)
        self.preview_video_seek_next_frame_button.setShown(True)
        self.preview_video_add_this_mark_button.setShown(True)
        self.menus_properties_panel_overlay_preview_button.setShown(False)
        clean_videos_list_selection(self)
        if self.selected_video:
            if self.preview_video_obj.state() == Phonon.PlayingState:
                self.preview_video_obj.stop()
            self.preview_video_widget.setShown(True)
        self.selected_menu = None

def change_aspect_ratio(self):
    for menu in self.list_of_menus:
        generate_preview_image(self, menu, self.dict_of_menus)

    for video in self.list_of_videos:
        generate_preview_image(self, video, self.dict_of_videos)

    if self.selected_aspect_ratio == 0:
        self.preview.setGeometry(50, 220, 720, 405)
        self.preview_video_widget.setGeometry(50, 180, 720, 405)
        self.nowediting_menus_panel_list.setIconSize(QtCore.QSize(100, 56))
        self.nowediting_videos_panel_list.setIconSize(QtCore.QSize(100, 56))
        self.options_panel_menu_buttons_x_position.setMaximum(720)
        self.options_panel_menu_buttons_width.setMaximum(720)
        self.menus_properties_panel_background_file_preview.setGeometry(10,50,89,50)
        self.menus_properties_panel_background_file_preview_background.setGeometry(0,0,self.menus_properties_panel_background_file_preview.width(),self.menus_properties_panel_background_file_preview.height())
        self.menus_properties_panel_background_file_preview_foreground.setGeometry(0,0,self.menus_properties_panel_background_file_preview.width(),self.menus_properties_panel_background_file_preview.height())
        self.menus_properties_panel_background_file_preview_foreground.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_background_file_preview_foreground_16_9.png'))
        self.menus_properties_panel_overlay_file_preview.setGeometry(110,50,89,50)
        self.menus_properties_panel_overlay_file_preview_background.setGeometry(0,0,self.menus_properties_panel_overlay_file_preview.width(),self.menus_properties_panel_overlay_file_preview.height())
        self.menus_properties_panel_overlay_file_preview_foreground.setGeometry(0,0,self.menus_properties_panel_overlay_file_preview.width(),self.menus_properties_panel_overlay_file_preview.height())
        self.menus_properties_panel_overlay_file_preview_foreground.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_background_file_preview_foreground_16_9.png'))
    elif self.selected_aspect_ratio == 1:
        self.preview.setGeometry(90, 220, 640, 480)
        self.preview_video_widget.setGeometry(90, 180, 640, 480)
        self.nowediting_menus_panel_list.setIconSize(QtCore.QSize(88, 66))
        self.nowediting_videos_panel_list.setIconSize(QtCore.QSize(88, 66))
        self.options_panel_menu_buttons_x_position.setMaximum(640)
        self.options_panel_menu_buttons_width.setMaximum(640)
        self.menus_properties_panel_background_file_preview.setGeometry(10,50,67,50)
        self.menus_properties_panel_background_file_preview_background.setGeometry(0,0,self.menus_properties_panel_background_file_preview.width(),self.menus_properties_panel_background_file_preview.height())
        self.menus_properties_panel_background_file_preview_foreground.setGeometry(0,0,self.menus_properties_panel_background_file_preview.width(),self.menus_properties_panel_background_file_preview.height())
        self.menus_properties_panel_background_file_preview_foreground.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_background_file_preview_foreground_4_3.png'))
        self.menus_properties_panel_overlay_file_preview.setGeometry(110,50,67,50)
        self.menus_properties_panel_overlay_file_preview_background.setGeometry(0,0,self.menus_properties_panel_overlay_file_preview.width(),self.menus_properties_panel_overlay_file_preview.height())
        self.menus_properties_panel_overlay_file_preview_foreground.setGeometry(0,0,self.menus_properties_panel_overlay_file_preview.width(),self.menus_properties_panel_overlay_file_preview.height())
        self.menus_properties_panel_overlay_file_preview_foreground.setPixmap(os.path.join(path_graphics, 'menus_properties_panel_background_file_preview_foreground_4_3.png'))

    self.options_panel_menu_buttons_y_position.setMaximum(int(self.video_formats[self.selected_video_format].split(' ')[1].split('x')[1]))
    self.options_panel_menu_buttons_height.setMaximum(int(self.video_formats[self.selected_video_format].split(' ')[1].split('x')[1]))

    self.no_preview_label.setGeometry(0,0,self.preview.width(),self.preview.height())

    if self.selected_menu:
        update_overlay_image_preview(self)

    populate_menus_list(self)
    populate_videos_list(self)

    update_changes(self)

def convert_to_timecode(value, framerate):
    value = value.replace('s', '')
    framerate = framerate.replace('s','')

    framerate = float(framerate.split('/')[1])/float(framerate.split('/')[0])

    if '/' in value:
        value = float(value.split('/')[0])/float(value.split('/')[1])
    else:
        value = float(value)

    value = value/framerate

    fr = int(str('%03d' % int(str(value).split('.')[1]))[:3])
    mm, ss = divmod(value, 60)
    hh, mm = divmod(mm, 60)

    return '%02d:%02d:%02d.%03d' % (hh, mm, ss, fr)

def convert_timecode_to_miliseconds(timecode):
    final_value = 0
    final_value += int(timecode.split(':')[2].split('.')[0])*1000
    final_value += int(timecode.split(':')[1])*60000
    final_value += int(timecode.split(':')[0])*3600000
    final_value += int(timecode.split('.')[-1])
    return final_value

def sort_list_of_chapters(dict_of_chapters):

    dict_of_chapters_for_order = {}
    for name in dict_of_chapters.keys():
        dict_of_chapters_for_order[dict_of_chapters[name]] = name
    list_of_chapters_in_order = sorted(dict_of_chapters_for_order.keys())

    new_list = []
    for timecode in list_of_chapters_in_order:
        new_list.append(dict_of_chapters_for_order[timecode])

    return new_list

def set_generate_dvd_kind(self):
    if not self.finalize_panel_generate_button_iso_checkbox.isChecked() and not self.finalize_panel_generate_button_ddp_checkbox.isChecked():
        self.finalize_panel_generate_button_iso_checkbox.setChecked(True)

###################################################################################################
############################################################################################# MENUS
###################################################################################################

def set_main_menu(self):
    self.dict_of_menus[self.selected_menu][6] = not self.dict_of_menus[self.selected_menu][6]

    for menu in self.list_of_menus:
        if not menu == self.selected_menu:
            self.dict_of_menus[menu][6] = False

    update_changes(self)

def choose_color(self):
    color = QtGui.QColorDialog().getColor()
    if color.isValid():
        self.dict_of_menus[self.selected_menu][4] = color.name()
    preview_overlay(self)
    update_changes(self)


def generate_preview_image(self, image_item, image_dict):
    if image_dict[image_item][0].split('.')[-1] in ['mov', 'm4v', 'mpg', 'm2v', 'mp4']:
        subprocess.call([ffmpeg_bin, '-loglevel', 'error', '-y', '-ss', '00:03.00', '-i', get_preview_file(self, image_dict[image_item][0]), '-frames:v', '1', os.path.join(path_tmp, image_item + '.preview_.png')])
        image_path = os.path.join(path_tmp, image_item + '.preview_.png')
    else:
        image_path = get_preview_file(self, image_dict[image_item][0])

    if self.selected_aspect_ratio == 0:
        size = '720x405!'
    elif self.selected_aspect_ratio == 1:
        size = '640x480!'
    subprocess.call([imagemagick_convert_bin, get_preview_file(self, image_path), '-resize', size, os.path.join(path_tmp, image_item + '.preview.png')])

def menu_selected(self):
    if self.nowediting_menus_panel_list.currentItem():
        self.nowediting_menus_panel_remove.setEnabled(True)
        self.nowediting_menus_panel_duplicate.setEnabled(True)
        self.selected_menu = self.nowediting_menus_panel_list.currentItem().text().split('\n')[0]
    else:
        self.nowediting_menus_panel_remove.setEnabled(False)
        self.nowediting_menus_panel_duplicate.setEnabled(False)
    #populate_menu_buttons_list(self)


    self.selected_menu_button = None
    self.options_panel_menu_buttons_position_box.setEnabled(False)
    self.options_panel_menu_buttons.setCurrentItem(None)

    self.preview_video_widget.setShown(False)

    nowediting_panel_button_changed(self, self.nowediting)
    populate_menu_buttons_list(self)
    clean_buttons_selection(self)
    update_changes(self)

def duplicate_menu(self):
    new_menu_name = check_name(self, self.list_of_menus, self.selected_menu)
    new_menu = copy.deepcopy(self.dict_of_menus[self.selected_menu])

    self.list_of_menus.append(new_menu_name)
    self.dict_of_menus[new_menu_name] = new_menu

    generate_preview_image(self, new_menu_name, self.dict_of_menus)

    self.selected_menu_button = None
    clean_menus_list_selection(self)

    self.selected_menu = self.list_of_menus[-1]
    update_changes(self)
    populate_menus_list(self)

    nowediting_panel_button_changed(self, self.nowediting)


def add_menu(self):
    image_path_list = QtGui.QFileDialog.getOpenFileNames(self, 'Select the image or video for menu', path_home, 'PNG, JPEG images or MPEG videos (*.jpg *.png *.m4v *.m2v *.mpg *.mp4 *.mov)')[0]#.toUtf8()

    for image_path_file in image_path_list:
        image_path = os.path.abspath(image_path_file)
        if not image_path == '':
            menu_name = check_name(self, self.list_of_menus, image_path.split('/')[-1].split('\\')[-1].split('.')[0])

            if len(self.list_of_menus) > 0:
                mainmenu = False
            else:
                mainmenu = True
            length = 60.0
            if image_path.endswith('.jpg') or image_path.endswith('.png') or image_path.endswith('.jpeg'):
                length = 60.0
            else:
                length_xml = unicode(subprocess.Popen([ffprobe_bin, '-loglevel', 'error',  '-show_format', '-print_format', 'xml', image_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read(), 'utf-8')
                length = float(length_xml.split(' duration="')[1].split('"')[0])

            self.list_of_menus.append(menu_name)
            self.dict_of_menus[menu_name] = [   image_path,                             # [0] Arquivo do fundo, imagem ou video
                                                [],                                     # [1] Lista de botoes
                                                {},                                     # [2] Dicionario de botoes
                                                None,                                   # [3] Arquivo de overlay (str)
                                                None,                                   # [4] Cor do Overlay (str)
                                                None,                                   # [5] Arquivo de som (str)
                                                mainmenu,                               # [6] Se é o menu principal
                                                .5,                                     # [7] Transparencia
                                                .5,                                     # [8] Borda dura
                                                length                                  # [9] Duracao em segundos
                                            ]

            generate_preview_image(self, menu_name, self.dict_of_menus)

    self.selected_menu_button = None
    clean_menus_list_selection(self)

    self.selected_menu = self.list_of_menus[-1]
    update_changes(self)
    populate_menus_list(self)

    nowediting_panel_button_changed(self, self.nowediting)

def check_name(self, names_list, name):
    final_name = name
    counter = 1
    while final_name in names_list:
         final_name = name + '_' + str(counter)
         counter += 1
    else:
        return final_name

def populate_menus_list(self):
    self.nowediting_menus_panel_list.clear()
    for menu in self.list_of_menus:
        icon = QtGui.QIcon(os.path.join(path_tmp, menu + '.preview.png'))
        self.nowediting_menus_panel_list.addItem(QtGui.QListWidgetItem(icon, menu))


def select_menu_file(self):
    image_path = QtGui.QFileDialog.getOpenFileName(self, 'Select the image or video for menu', path_home, 'PNG, JPEG images or MPEG videos (*.jpg *.png *.m4v *.m2v *.mpg *.mp4 *.mov)')[0]#.toUtf8()
    if not image_path == '':
        self.dict_of_menus[self.selected_menu][0] = image_path

    generate_preview_image(self, self.selected_menu, self.dict_of_menus)
    populate_menus_list(self)
    update_changes(self)


def select_overlay_file(self):
    overlay_image_path = QtGui.QFileDialog.getOpenFileName(self, "Select an image for the overlay", path_home, "Images (*.jpg *.png)")[0]#.toUtf8()
    if not overlay_image_path == '':
        self.dict_of_menus[self.selected_menu][3] = overlay_image_path
    update_overlay_image_preview(self)


def update_overlay_image_preview(self):
    preview_overlay(self)
    update_changes(self)

def preview_overlay_clicked(self):
    self.overlay_preview = not self.overlay_preview
    preview_overlay(self)

def preview_overlay(self):
    if self.selected_aspect_ratio == 0:
        size = '720x405!'
    elif self.selected_aspect_ratio == 1:
        size = '640x480!'

    for menu in self.list_of_menus:
        if self.dict_of_menus[menu][3]:
            menu_color = '#FFFFFF'
            if self.dict_of_menus[menu][4]:
                menu_color = self.dict_of_menus[menu][4]
            subprocess.call([imagemagick_convert_bin, get_preview_file(self, self.dict_of_menus[menu][3]), '-resize', size, '+antialias', '-threshold', str(int(self.dict_of_menus[menu][8]*100)) + '%', '-flatten', os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl.preview.png')])
            subprocess.call([imagemagick_convert_bin, os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl.preview.png'), '-threshold', str(int(self.dict_of_menus[menu][8]*100)) + '%', '-transparent', 'white', '-channel', 'RGBA', '-fill', menu_color + str('%02x' % int(self.dict_of_menus[menu][7]*255)), '-opaque', 'black', os.path.join(path_tmp, self.dict_of_menus[menu][3].split('/')[-1].split('\\')[-1][:-4] + '_hl.preview.png')])

    update_changes(self)

def preview_directions(self):
    self.directions_preview = not self.directions_preview
    update_changes(self)

def select_menu_sound_file(self):
    menu_sound_path = QtGui.QFileDialog.getOpenFileName(self, "Select an audio file", path_home, "Audio file (*.ac3 *.flac)")[0]
    if not menu_sound_path == '':
        self.dict_of_menus[self.selected_menu][5] = menu_sound_path
        self.menus_properties_panel_sound_label.setText(menu_sound_path.split('/')[-1].split('\\')[-1])

def remove_menu(self):
    self.list_of_menus.remove(self.selected_menu)
    del self.dict_of_menus[self.selected_menu]

    if len(self.list_of_menus) == 1:
        self.dict_of_menus[self.list_of_menus[0]][6] = True

    for menu in self.list_of_menus:
        for button in self.dict_of_menus[menu][1]:
            print self.dict_of_menus[menu][2][button][4]
            if self.dict_of_menus[menu][2][button][4] == self.selected_menu:
                self.dict_of_menus[menu][2][button][4] = None

    clean_menus_list_selection(self)
    populate_menus_list(self)
    update_changes(self)

def clean_menus_list_selection(self):
    self.selected_menu = None
    self.no_preview_label.setShown(True)
    self.nowediting_menus_panel_list.setCurrentItem(None)
    self.nowediting_menus_panel_duplicate.setEnabled()
    self.nowediting_menus_panel_remove.setEnabled()
    clean_buttons_selection(self)



def transparency_slider_changing(self):
    self.menus_properties_panel_transparency_slider_value.setText(str(int(self.menus_properties_panel_transparency_slider.value())) + '%')

def transparency_slider_changed(self):
    self.dict_of_menus[self.selected_menu][7] = self.menus_properties_panel_transparency_slider.value()/100.0
    preview_overlay(self)

def border_slider_changing(self):
    self.menus_properties_panel_border_slider_value.setText(str(int(self.menus_properties_panel_border_slider.value())) + '%')

def border_slider_changed(self):
    self.dict_of_menus[self.selected_menu][8] = self.menus_properties_panel_border_slider.value()/100.0
    preview_overlay(self)

###################################################################################################
########################################################################################### BUTTONS
###################################################################################################

def add_menu_button(self):
    new_button_name = check_name(self, self.dict_of_menus[self.selected_menu][1], 'button')
    self.dict_of_menus[self.selected_menu][1].append(new_button_name)
    self.dict_of_menus[self.selected_menu][2][new_button_name] = [  10,             # posição X
                                                                    10,             # posição Y
                                                                    50,             # largura
                                                                    50,             # altura
                                                                    None,           # jump to
                                                                    [   None,       # top direction
                                                                        None,       # right direction
                                                                        None,       # bottom direction
                                                                        None        # left direction
                                                                    ]
                                                                ]
    populate_menu_buttons_list(self)
    update_jumpto_list(self)
    update_changes(self)

def menu_button_selected(self):
    self.options_panel_menu_buttons_position_box.setEnabled(True)
    self.selected_menu_button = self.options_panel_menu_buttons.currentItem().text()
    self.options_panel_menu_buttons_remove.setEnabled(True)
    self.options_panel_menu_buttons_edit.setEnabled(True)
    update_changes(self)

def menu_buttons_set_geometry(self):
    final_list = [self.options_panel_menu_buttons_x_position.value(), self.options_panel_menu_buttons_y_position.value(), self.options_panel_menu_buttons_width.value(), self.options_panel_menu_buttons_height.value(), self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][4], self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5]]
    self.dict_of_menus[self.selected_menu][2][self.selected_menu_button] = final_list
    update_changes(self)

def populate_menu_buttons_list(self):
    self.options_panel_menu_buttons.clear()
    self.options_panel_menu_buttons_edit.setText('')
    print self.selected_menu
    print self.dict_of_menus[self.selected_menu][1]
    for button in self.dict_of_menus[self.selected_menu][1]:
        self.options_panel_menu_buttons.addItem(button)

def populate_button_directions_list(self):
    final_list = ["Auto"]
    for button in self.dict_of_menus[self.selected_menu][1]:
        if not button == self.selected_menu_button:
            final_list.append(button)
    self.options_panel_menu_buttons_directions_top.clear()
    self.options_panel_menu_buttons_directions_top.addItems(final_list)
    self.options_panel_menu_buttons_directions_right.clear()
    self.options_panel_menu_buttons_directions_right.addItems(final_list)
    self.options_panel_menu_buttons_directions_bottom.clear()
    self.options_panel_menu_buttons_directions_bottom.addItems(final_list)
    self.options_panel_menu_buttons_directions_left.clear()
    self.options_panel_menu_buttons_directions_left.addItems(final_list)

def remove_menu_button(self):
    del self.dict_of_menus[self.selected_menu][2][self.selected_menu_button]
    self.dict_of_menus[self.selected_menu][1].remove(self.selected_menu_button)

    for menu in self.list_of_menus:
        for button in self.dict_of_menus[menu][1]:
            directions_list = self.dict_of_menus[menu][2][button][5]
            for i in range(len(directions_list)):
                if directions_list[i] == self.selected_menu_button:
                    directions_list[i] = None
            self.dict_of_menus[menu][2][button][5] = directions_list

    populate_menu_buttons_list(self)
    clean_buttons_selection(self)

def edit_menu_button(self):
    self.options_panel_menu_buttons.setEnabled(False)
    self.options_panel_menu_buttons_remove.setEnabled(False)
    self.options_panel_menu_buttons_add.setEnabled(False)
    self.options_panel_menu_buttons_position_box.setEnabled(False)
    self.options_panel_menu_buttons_edit_field.setVisible(True)
    self.options_panel_menu_buttons_edit_confirm.setVisible(True)
    self.options_panel_menu_buttons_edit_cancel.setVisible(True)
    self.options_panel_menu_buttons_edit.setText(self.selected_menu_button)

    self.options_panel_menu_buttons_edit_field

def edit_field_menu_changed(self):
    if self.options_panel_menu_buttons_edit_field.text() in self.dict_of_menus[self.selected_menu][1]:
        self.options_panel_menu_buttons_edit_confirm.setEnabled(False)
    else:
        self.options_panel_menu_buttons_edit_confirm.setEnabled(True)

def edit_confirm_menu_button(self):
    old_menu_button_name = self.selected_menu_button
    old_menu_button = self.dict_of_menus[self.selected_menu][2][self.selected_menu_button]
    self.dict_of_menus[self.selected_menu][2][self.options_panel_menu_buttons_edit_field.text()] = old_menu_button
    self.dict_of_menus[self.selected_menu][1].append(self.options_panel_menu_buttons_edit_field.text())

    del self.dict_of_menus[self.selected_menu][2][old_menu_button_name]
    self.dict_of_menus[self.selected_menu][1].remove(old_menu_button_name)

    self.dict_of_menus[self.selected_menu][1]

    for button in self.dict_of_menus[self.selected_menu][1]:
        direction_index = 0
        for direction in self.dict_of_menus[self.selected_menu][2][button][5]:
            if direction == old_menu_button_name:
                self.dict_of_menus[self.selected_menu][2][button][5][direction_index] = self.options_panel_menu_buttons_edit_field.text()
            direction_index += 1

    populate_menu_buttons_list(self)
    clean_buttons_selection(self)

def edit_cancel_menu_button(self):
    self.options_panel_menu_buttons_edit_field.setVisible(False)
    self.options_panel_menu_buttons_edit_confirm.setVisible(False)
    self.options_panel_menu_buttons_edit_cancel.setVisible(False)
    populate_menu_buttons_list(self)
    clean_buttons_selection(self)

def clean_buttons_selection(self):
    self.options_panel_menu_buttons.setEnabled(True)
    self.options_panel_menu_buttons_add.setEnabled(True)
    self.options_panel_menu_buttons_edit_field.setText('')
    self.selected_menu_button = None
    self.options_panel_menu_buttons.setCurrentItem(None)
    self.options_panel_menu_buttons_remove.setEnabled(False)
    self.options_panel_menu_buttons_position_box.setEnabled(False)
    self.options_panel_menu_buttons_edit.setEnabled(False)
    self.options_panel_menu_buttons_x_position.setValue(0)
    self.options_panel_menu_buttons_y_position.setValue(0)
    self.options_panel_menu_buttons_width.setValue(0)
    self.options_panel_menu_buttons_height.setValue(0)
    update_changes(self)

def button_directions_selected(self):
    directions_list = [None,None,None,None]
    if not self.options_panel_menu_buttons_directions_top.currentText() == 'Auto':
        directions_list[0] = self.options_panel_menu_buttons_directions_top.currentText()
    if not self.options_panel_menu_buttons_directions_right.currentText() == 'Auto':
        directions_list[1] = self.options_panel_menu_buttons_directions_right.currentText()
    if not self.options_panel_menu_buttons_directions_bottom.currentText() == 'Auto':
        directions_list[2] = self.options_panel_menu_buttons_directions_bottom.currentText()
    if not self.options_panel_menu_buttons_directions_left.currentText() == 'Auto':
        directions_list[3] = self.options_panel_menu_buttons_directions_left.currentText()
    self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][5] = directions_list
    update_changes(self)

###################################################################################################
############################################################################################ VIDEOS
###################################################################################################

def update_timeline(self):
    #self.videos_player_controls_panel_current_time.setText('<font style="font-size:22px;font-family=' + '"Ubuntu Mono"' + ';color:#9AC3CF">' + convert_to_timecode(str(self.preview_video_obj.currentTime()),'1/1000') + '</font>')
    self.videos_player_controls_panel_current_time.setText(convert_to_timecode(str(self.preview_video_obj.currentTime()),'1/1000'))
    self.videos_player_timeline.update()

def add_video(self):
    video_path_list = QtGui.QFileDialog.getOpenFileNames(self, "Selecione um video", path_home, "Video files (*.m4v *.m2v *.mpg *.mp4 *.mov)")[0]

    for video_path_file in video_path_list:
        video_path = os.path.abspath(video_path_file)
        if not video_path == '':
            video_name = video_path.split('/')[-1].split('\\')[-1].split('.')[0]

            chapters_list, chapters_dict = get_video_chapters(self, video_path)

            length_xml = unicode(subprocess.Popen([ffprobe_bin, '-loglevel', 'error', '-show_format', '-print_format', 'xml', video_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read(), 'utf-8')
            length = float(length_xml.split(' duration="')[1].split('"')[0])

            self.dict_of_videos[video_name] =   [   video_path,                   # [0] Caminho do video
                                                    chapters_list,                # [1] Lista de capítulos
                                                    chapters_dict,                # [2] Dict de capítulos
                                                    False,                        # [3] se é o video de intro
                                                    True,                         # [4] se é para ser reconvertido
                                                    length,                       # [5] Duração
                                                    None,                         # [6] Post
                                                    0                             # [7] Resolução
                                                ]
            self.list_of_videos.append(video_name)

            generate_preview_image(self, video_name, self.dict_of_videos)

    populate_videos_list(self)

def populate_videos_list(self):
    self.nowediting_videos_panel_list.clear()
    for video in self.list_of_videos:
        icon = QtGui.QIcon(os.path.join(path_tmp, video + '.preview.png'))
        self.nowediting_videos_panel_list.addItem(QtGui.QListWidgetItem(icon, video))

def update_jumpto_list(self):
    self.list_of_jumpto = []
    for video in self.dict_of_videos.keys():
        self.list_of_jumpto.append(video)
    for menu in self.list_of_menus:
        self.list_of_jumpto.append(menu)

def remove_video(self):
    del self.dict_of_videos[self.selected_video]
    self.list_of_videos.remove(self.selected_video)

    for menu in self.list_of_menus:
        for button in self.dict_of_menus[menu][1]:
            if self.dict_of_menus[menu][2][button][4] == self.selected_video:
                self.dict_of_menus[menu][2][button][4] = None

    clean_videos_list_selection(self)
    populate_videos_list(self)

def clean_videos_list_selection(self):
    self.selected_video = None
    self.no_preview_label.setShown(True)
    self.nowediting_videos_panel_list.setCurrentItem(None)

def video_selected(self):
    if self.nowediting_videos_panel_list.currentItem():
        self.nowediting_videos_panel_remove.setEnabled(True)
        self.selected_video = self.nowediting_videos_panel_list.currentItem().text()
    else:
        self.nowediting_videos_panel_remove.setEnabled(False)


    self.preview_video_widget.setShown(True)
    self.preview_video_obj.setCurrentSource(Phonon.MediaSource(get_preview_file(self, self.dict_of_videos[self.selected_video][0])))

    nowediting_panel_button_changed(self, self.nowediting)

    update_changes(self)

def button_jumpto_selected(self):
    self.dict_of_menus[self.selected_menu][2][self.selected_menu_button][4] = self.options_panel_menu_buttons_jumpto.currentText()

def video_play(self):
    self.preview_video_obj.play()

def video_pause(self):
    self.videos_player_controls_panel_pause_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_pause_press.png'))
    self.videos_player_controls_panel_play_background.setPixmap(os.path.join(path_graphics, 'videos_player_controls_panel_play_press.png'))
    self.preview_video_obj.pause()

def video_stop(self):
    self.preview_video_obj.stop()
    update_timeline(self)

def video_seek_next_frame(self, position):
    self.preview_video_obj.seek(self.preview_video_obj.currentTime() + position)
    update_timeline(self)

def video_seek_back_frame(self, position):
    self.preview_video_obj.seek(self.preview_video_obj.currentTime() - position)
    update_timeline(self)

def video_add_this_mark_frame(self):
    self.selected_video_chapter = None
    append_chapter(self, check_name(self, self.dict_of_videos[self.selected_video][1], 'mark'), convert_to_timecode(str(self.preview_video_obj.currentTime()), '1/1000'))
    update_changes(self)

def populate_jumpto(self):
    self.options_panel_menu_buttons_jumpto.clear()
    final_list = []
    for menu in self.list_of_menus:
        final_list.append(menu)
    for video in self.list_of_videos:
        final_list.append(video)
        for chapter in sort_list_of_chapters(self.dict_of_videos[video][2]):
            final_list.append(video + ' > ' + str(chapter) + ' (' + self.dict_of_videos[video][2][chapter] + ')')
        list_of_chapter_groups = []
        for chapter in sort_list_of_chapters(self.dict_of_videos[video][2]):
            if not str(chapter).split(' ')[0] in list_of_chapter_groups:
                list_of_chapter_groups.append(str(chapter).split(' ')[0])
                final_list.append(video + ' > ' + str(chapter).split(' ')[0])
    self.options_panel_menu_buttons_jumpto.addItems(final_list)

def set_intro_video(self):
    self.dict_of_videos[self.selected_video][3] = self.options_panel_video_intro_video_checkbox.isChecked()

    for video in self.list_of_videos:
        if not video == self.selected_video:
            self.dict_of_videos[video][3] = False

def set_reencode_video(self):
    self.dict_of_videos[self.selected_video][4] = self.options_panel_video_reencode_video_checkbox.isChecked()
    update_changes(self)

def video_resolution_combo_selected(self):
    self.dict_of_videos[self.selected_video][7] = self.options_panel_video_resolution_combo.currentIndex()

def video_jumpto_selected(self):
    if self.options_panel_video_jumpto.currentText() == 'Main menu':
        self.dict_of_videos[self.selected_video][6] = None
    else:
        self.dict_of_videos[self.selected_video][6] = self.options_panel_video_jumpto.currentText()

def populate_jumpto_list(self):
    final_list = ['Main menu']
    final_list += self.list_of_menus
    final_list += self.list_of_videos
    final_list.remove(self.selected_video)
    self.options_panel_video_jumpto.clear()
    self.options_panel_video_jumpto.addItems(final_list)

###################################################################################################
########################################################################################## CHAPTERS
###################################################################################################

def import_chapters(self):
    filepath = QtGui.QFileDialog.getOpenFileName(self, "Select a video or XML", path_home, "Video files (*.fcpxml *.m4v *.m2v *.mpg *.mp4 *.mov)")[0]#.toUtf8()
    if not filepath == '':
        chapters_list, chapters_dict = get_video_chapters(self, filepath)

        self.dict_of_videos[self.selected_video][1] = self.dict_of_videos[self.selected_video][1] + chapters_list
        for chapter in chapters_dict.keys():
            self.dict_of_videos[self.selected_video][2][chapter] = chapters_dict[chapter]

        populate_chapters_list(self)

def get_video_chapters(self, filepath):
    chapters_list = []
    chapters_dict = {}
    if filepath.split('.')[-1] == 'fcpxml':
        chapters_xml = codecs.open(filepath, 'r', 'utf-8').read()
        for chapter_line in chapters_xml.split('<chapter-marker ')[1:]:
            if '/>' in chapter_line and ('start="' in chapter_line.split('/>')[0] and 'duration="' in chapter_line.split('/>')[0]):
                mark = convert_to_timecode(chapter_line.split('start="')[1].split('"')[0], chapter_line.split('duration="')[1].split('"')[0])
                name = check_name(self, chapters_list, chapter_line.split('value="')[1].split('"')[0])
                chapters_list.append(name)
                chapters_dict[name] = mark
    else:
        chapters_xml = unicode(subprocess.Popen([ffprobe_bin, '-loglevel', 'error', '-show_chapters', '-print_format', 'xml', filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read(), 'utf-8')
        for chapter_line in chapters_xml.split('<chapter '):
            if '</chapter>' in chapter_line:
                mark = convert_to_timecode(chapter_line.split('start="')[1].split('"')[0], chapter_line.split('time_base="')[1].split('"')[0])
                name = check_name(self, chapters_list, chapter_line.split('value="')[1].split('"')[0])
                chapters_list.append(name)
                chapters_dict[name] = mark

    return chapters_list, chapters_dict

def chapter_selected(self):
    self.selected_video_chapter = self.options_panel_video_chapters_list.currentItem().text().split('\n')[0]
    self.options_panel_video_chapters_remove.setEnabled(True)
    self.options_panel_video_chapters_edit.setEnabled(True)
    chapter_seek_in_timeline(self)

def chapter_seek_in_timeline(self):
    self.preview_video_obj.seek(convert_timecode_to_miliseconds(self.dict_of_videos[self.selected_video][2][self.selected_video_chapter]))

def add_chapter(self):
    self.selected_video_chapter = None
    self.options_panel_video_chapters_timecode.setText('')
    self.options_panel_video_chapters_name.setText('')
    show_edit_chapter(self)

def append_chapter(self, name, timecode):
    if self.selected_video_chapter:
        self.dict_of_videos[self.selected_video][1].remove(self.selected_video_chapter)
        del self.dict_of_videos[self.selected_video][2][self.selected_video_chapter]
    self.dict_of_videos[self.selected_video][1].append(name)
    self.dict_of_videos[self.selected_video][2][name] = timecode

def confirm_edit_chapter(self):
    append_chapter(self, self.options_panel_video_chapters_name.text(), self.options_panel_video_chapters_timecode.text())
    hide_edit_chapter(self)
    update_changes(self)

def check_chapter_name(self):
    None

def hide_edit_chapter(self):
    self.options_panel_video_chapters_list.setGeometry(10,70,self.options_panel_video_panel.width()-20,self.options_panel_video_panel.height()-115)
    self.options_panel_video_chapters_list.setEnabled(True)
    self.options_panel_video_chapters_name_label.setShown(False)
    self.options_panel_video_chapters_name.setShown(False)
    self.options_panel_video_chapters_timecode_label.setShown(False)
    self.options_panel_video_chapters_timecode.setShown(False)
    self.options_panel_video_chapters_edit_confirm.setShown(False)
    self.options_panel_video_chapters_edit_cancel.setShown(False)
    self.options_panel_video_chapters_add.setShown(True)
    self.options_panel_video_chapters_remove.setShown(True)
    self.options_panel_video_chapters_edit.setShown(True)
    self.options_panel_video_chapters_import.setShown(True)

def remove_chapter(self):
    del self.dict_of_videos[self.selected_video][2][self.selected_video_chapter]
    self.dict_of_videos[self.selected_video][1].remove(self.selected_video_chapter)
    self.selected_video_chapter = None
    update_changes(self)

def edit_chapter(self):
    self.options_panel_video_chapters_name.setText(self.selected_video_chapter)
    self.options_panel_video_chapters_timecode.setText(self.dict_of_videos[self.selected_video][2][self.selected_video_chapter])
    check_chapter_name(self)
    show_edit_chapter(self)

def show_edit_chapter(self):
    self.options_panel_video_chapters_list.setGeometry(10,70,self.options_panel_video_panel.width()-20,self.options_panel_video_panel.height()-135)
    self.options_panel_video_chapters_list.setEnabled(False)
    self.options_panel_video_chapters_name_label.setShown(True)
    self.options_panel_video_chapters_name.setShown(True)
    self.options_panel_video_chapters_timecode_label.setShown(True)
    self.options_panel_video_chapters_timecode.setShown(True)
    self.options_panel_video_chapters_edit_confirm.setShown(True)
    self.options_panel_video_chapters_edit_cancel.setShown(True)
    self.options_panel_video_chapters_add.setShown(False)
    self.options_panel_video_chapters_remove.setShown(False)
    self.options_panel_video_chapters_edit.setShown(False)
    self.options_panel_video_chapters_import.setShown(False)

def populate_chapters_list(self):
    self.options_panel_video_chapters_list.clear()
    list_of_chapters_in_order = sort_list_of_chapters(self.dict_of_videos[self.selected_video][2])

    self.dict_of_videos[self.selected_video][1] = list_of_chapters_in_order

    for chapter in self.dict_of_videos[self.selected_video][1]:
        icon = QtGui.QIcon(os.path.join(path_graphics, 'chapter.png'))
        self.options_panel_video_chapters_list.addItem(QtGui.QListWidgetItem(icon, unicode(str(chapter), 'utf-8') + '\n' + self.dict_of_videos[self.selected_video][2][chapter]))

###################################################################################################
###################################################################################### GENERATE DVD
###################################################################################################

def dvd_generate(self):
    self.preview_video_widget.setShown(False)
    if not self.actual_project_file:
        self.generate_dvd_thread_thread.actual_project_file = os.path.join(path_home, self.project_name + '.odvdp')
    else:
        self.generate_dvd_thread_thread.actual_project_file = self.actual_project_file
        self.generate_dvd_thread_thread.project_name = self.project_name

    if self.audio_formats[self.selected_audio_format] == 'MP2 48kHz':
        self.generate_dvd_thread_thread.audio_codec = 'pcm_s16le'

    if self.video_formats[self.selected_video_format].split(' ')[0] == 'NTSC':
        self.generate_dvd_thread_thread.framerate = '29.97'

    self.generate_dvd_thread_thread.height = int(self.video_formats[self.selected_video_format].split(' ')[1].split('x')[1])
    self.generate_dvd_thread_thread.video_format = self.video_formats[self.selected_video_format].split(' ')[0].lower()
    self.generate_dvd_thread_thread.video_resolutions = self.resolutions#self.video_formats[self.selected_video_format].split(' ')[1].lower()

    self.generate_dvd_thread_thread.aspect_ratio = self.aspect_ratios[self.selected_aspect_ratio]

    self.generate_dvd_thread_thread.selected_menu_encoding = self.selected_menu_encoding
    self.generate_dvd_thread_thread.selected_video_encoding = self.selected_video_encoding

    self.generate_dvd_thread_thread.selected_menu_twopass = self.selected_menu_twopass
    self.generate_dvd_thread_thread.selected_video_twopass = self.selected_video_twopass

    self.generate_dvd_thread_thread.selected_gop_size = self.selected_gop_size
    self.generate_dvd_thread_thread.selected_menu_bitrate = self.selected_menu_bitrate
    self.generate_dvd_thread_thread.selected_menu_max_bitrate = self.selected_menu_max_bitrate
    self.generate_dvd_thread_thread.selected_video_bitrate = self.selected_video_bitrate
    self.generate_dvd_thread_thread.selected_video_max_bitrate = self.selected_video_max_bitrate

    self.generate_dvd_thread_thread.list_of_menus = self.list_of_menus
    self.generate_dvd_thread_thread.list_of_videos = self.list_of_videos
    self.generate_dvd_thread_thread.dict_of_menus = self.dict_of_menus
    self.generate_dvd_thread_thread.dict_of_videos = self.dict_of_videos

    self.generate_dvd_thread_thread.has_menus = self.has_menus

    self.generate_dvd_thread_thread.audio_datarate = int(self.selected_audio_datarate.split(' ')[0])

    self.generate_dvd_thread_thread.generate_ddp = self.finalize_panel_generate_button_ddp_checkbox.isChecked()
    self.generate_dvd_thread_thread.generate_iso = self.finalize_panel_generate_button_iso_checkbox.isChecked()

    self.generate_dvd_thread_thread.start()

def generate_effect(self, widget, effect_type, duration, startValue, endValue):
    widget.setDuration(duration)
    if effect_type == 'geometry':
        widget.setStartValue(QtCore.QRect(startValue[0],startValue[1],startValue[2],startValue[3]))
        widget.setEndValue(QtCore.QRect(endValue[0],endValue[1],endValue[2],endValue[3]))
    elif effect_type == 'opacity':
        widget.setStartValue(startValue)
        widget.setEndValue(endValue)
    widget.start()

app = QtGui.QApplication(sys.argv)
app.addLibraryPath(app.applicationDirPath() + "/../PlugIns")
#app.setStyle("clearlooks")
app.setStyle("plastique")
app.setApplicationName("Open DVD Producer")
font_database = QtGui.QFontDatabase()
font_database.addApplicationFont(os.path.join(path_opendvdproducer, 'Ubuntu-RI.ttf'))
font_database.addApplicationFont(os.path.join(path_opendvdproducer, 'Ubuntu-R.ttf'))
font_database.addApplicationFont(os.path.join(path_opendvdproducer, 'Ubuntu-B.ttf'))
font_database.addApplicationFont(os.path.join(path_opendvdproducer, 'Ubuntu-BI.ttf'))
font_database.addApplicationFont(os.path.join(path_opendvdproducer, 'UbuntuMono-R.ttf'))
app.setFont(QtGui.QFont('Ubuntu', interface_font_size))
app.setDesktopSettingsAware(False)
app.main = main_window()

app.main.show()

sys.exit(app.exec_())
