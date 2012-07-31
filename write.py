"""
/!\ REQUIRES /!\  PIL with _imagingfont module
you can find a precompiled version for windows here: http://www.lfd.uci.edu/~gohlke/pythonlibs/#pil

*** USAGE ***

To write text, use the /write command.
The first block you place after this command marks the top left corner of the written text
Example: To write the text "Ace of Spades":
      /write Ace of Spades

To set the font, use the /writefont command.
This is the file name of the TrueType font to use without the ".ttf" extension.
To find font file names in windows: open Fonts from control panel, right click the font you want and select Properties
Example: To set the font to Harrington Regular:
      /writefont HARNGTON

To set the font size, use the /writesize command.
Example:
      /writesize 20
"""

from pyspades.contained import BlockAction, SetColor
from pyspades.constants import *
from commands import add, admin
from itertools import product
from cbc import cbc

from PIL import Image, ImageFont, ImageDraw

@admin
def write(connection, *text):
    connection.write_text = ' '.join(text)
    if connection.write_text != '':
        connection.writing = True
        return 'The next block you place will write: ' + connection.write_text
    else:
        connection.writing = False
        return 'Writing cancelled'

@admin
def writefont(connection, *font):
    font = ' '.join(font)
    try:
        ImageFont.truetype(font + '.ttf', connection.write_size)
    except IOError:
        return "Font doesn't exist: %s" % font
    connection.write_fontname = font
    return 'Writing in font %s' % font

@admin
def writesize(connection, ptsize):
    ptsize = abs(int(ptsize))
    if ptsize > 3:
        connection.write_size = ptsize
        return 'Writing in size %i' % ptsize

add(write)
add(writefont)
add(writesize)

def apply_script(protocol, connection, config):
    cbc.set_protocol(protocol)
    
    class WriterConnection(connection):
        def __init__(self, *arg, **kw):
            connection.__init__(self, *arg, **kw)
            self.writing = False
            self.write_text = ''
            self.write_fontname = 'Arial'
            self.write_size = 10
        
        def image_generator(self, pixels, width, height, z, color = None):
            block_action = BlockAction()
            block_action.player_id = self.player_id
            block_action.value = BUILD_BLOCK
            
            # todo: vertical images, rotate text
            
            for x, y in product(xrange(width), xrange(height)):
                if pixels[x,y][3] != 0:
                    block_action.x, block_action.y, block_action.z = x, y, z
                    self.protocol.send_contained(block_action, save = True)
                    self.protocol.map.set_point(x, y, z, (color if color is not None else pixels[x,y][:3] + (255,)))
                    yield 1, 0
        
        def on_block_build_attempt(self, x, y, z):
            if self.writing:
                self.writing = False
                font = ImageFont.truetype(self.write_fontname + '.ttf', self.write_size)
                width = height = 512
                im = Image.new('RGBA', (width, height), (0,0,0,0))
                draw = ImageDraw.Draw(im)
                draw.fontmode = "1"
                draw.text((x, y), self.write_text, fill='Black', font=font)
                pixels = im.load()
                
                cbc.add(self.image_generator(pixels, width, height, z, self.color + (255,)))
                return False
            return connection.on_block_build_attempt(self, x, y, z)
    
    return protocol, WriterConnection
