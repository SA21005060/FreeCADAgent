from FreeCAD import Vector, Placement, Rotation
import Part
import FreeCAD as App

# 参数定义（模块化，可直接修改）
flange_outer_r = 50
flange_thickness = 10
bolt_hole_r = 4
bolt_circle_r = 40
num_holes = 6

# 创建/获取文档
if not App.ActiveDocument:
    doc = App.newDocument("Flange")
else:
    doc = App.ActiveDocument

# 创建法兰主体
body = Part.makeCylinder(flange_outer_r, flange_thickness)
body_obj = doc.addObject("Part::Feature", "Flange_Body")
body_obj.Shape = body

# 创建6个均匀分布的螺栓孔
holes = []
angle_step = 360 / num_holes
for i in range(num_holes):
    angle = i * angle_step
    x = bolt_circle_r * App.Math.cos(App.Math.radians(angle))
    y = bolt_circle_r * App.Math.sin(App.Math.radians(angle))
    pos = Vector(x, y, 0)
    hole = Part.makeCylinder(bolt_hole_r, flange_thickness, pos)
    hole_obj = doc.addObject("Part::Feature", f"Bolt_Hole_{i+1}")
    hole_obj.Shape = hole
    holes.append(hole_obj)

# 布尔运算切除螺栓孔
fuse_holes = doc.addObject("Part::MultiFuse", "All_Bolt_Holes")
fuse_holes.Shapes = holes
final = doc.addObject("Part::Cut", "Flange_Final")
final.Base = body_obj
final.Tool = fuse_holes

# 刷新并显示
doc.recompute()
Part.show(final.Shape)
