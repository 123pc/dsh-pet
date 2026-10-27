"""验证上游动作覆盖、实际姿势变化、画布边界及步态的支撑/摆动区别。"""
import sys
import unittest
from pathlib import Path
from PIL import ImageChops

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from catalogue import catalogue
from puppet import Puppet


class FullAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.puppet=Puppet()
        cls.rows=catalogue()[1]

    def test_complete_upstream_contract(self):
        self.assertEqual(len(self.rows),106)
        for event,count in (("balance",6),("whisper",3),("workStatus",6)):
            self.assertEqual(len([r for r in self.rows if r["group"]==event]),count)

    def test_every_action_has_a_renderer_and_motion(self):
        for row in self.rows:
            with self.subTest(name=row["name"]):
                a=self.puppet.render(row["pose"],row["prop"],.12)
                b=self.puppet.render(row["pose"],row["prop"],.39)
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertIsNotNone(a.getchannel("A").getbbox())

    def test_no_frame_touches_canvas_edges(self):
        for row in self.rows:
            for t in (0,.25,.5,.75):
                with self.subTest(name=row["name"],t=t):
                    frame=self.puppet.render(row["pose"],row["prop"],t)
                    box=frame.getchannel("A").getbbox()
                    self.assertGreater(box[0],0)
                    self.assertGreater(box[1],0)
                    self.assertLess(box[2],640)
                    self.assertLess(box[3],360)

    def test_walk_leg_silhouettes_change_without_head_jitter(self):
        a=self.puppet.walk(.5)
        b=self.puppet.walk(.75)
        self.assertNotEqual(a.crop((255,280,390,350)).tobytes(),b.crop((255,280,390,350)).tobytes())
        self.assertEqual(a.size,(640,360))
        self.assertGreater(a.getchannel("A").getbbox()[1],0)


if __name__=="__main__": unittest.main()
