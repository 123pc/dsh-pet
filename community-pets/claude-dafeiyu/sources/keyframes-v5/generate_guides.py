from PIL import Image,ImageDraw
from pathlib import Path
root=Path(__file__).resolve().parent / 'guides'
poses={
'back': ([(430,700),(600,850),(720,1020)],[(380,700),(220,850),(100,1020)]),
'forward': ([(430,700),(270,850),(120,1020)],[(380,700),(530,850),(650,1020)]),
'back-mid': ([(430,700),(540,870),(640,1040)],[(380,700),(280,870),(200,1040)]),
'forward-mid': ([(430,700),(320,870),(230,1040)],[(380,700),(480,870),(580,1040)]),
'neutral': ([(430,700),(450,890),(480,1060)],[(380,700),(350,890),(330,1060)])}
for name,(near,far) in poses.items():
 im=Image.new('RGB',(1024,1536),'white');d=ImageDraw.Draw(im)
 d.ellipse((150,120,650,650),outline='#dddddd',width=6)
 d.rectangle((270,680,530,1070),outline='#dddddd',width=5)
 d.line(far,fill='#dd8b33',width=25,joint='curve')
 d.line(near,fill='#2678bf',width=30,joint='curve')
 for pts,col in [(far,'#dd8b33'),(near,'#2678bf')]:
  for x,y in pts:d.ellipse((x-18,y-18,x+18,y+18),fill=col)
 d.text((40,1130),'BLUE = NEAR ARM, drawn in FRONT of torso',fill='#165c9d')
 d.text((40,1170),'ORANGE = FAR ARM, drawn BEHIND torso',fill='#995522')
 d.text((40,1210),'Both hands remain LOW at skirt-hem level. Natural loose elbows.',fill='black')
 d.text((40,1250),'Diagram only. Preserve the target character head, body and legs.',fill='black')
 im.save(root/(name+'.png'))
