import FreeCAD as App
import FreeCADGui as Gui
import Part
from FreeCAD import Vector

doc = App.newDocument("DemoHouse")

house_length = 100.0
house_width = 80.0
house_height = 60.0
roof_height = 40.0

house_body = Part.makeBox(house_length, house_width, house_height)
body_obj = doc.addObject("Part::Feature", "HouseBody")
body_obj.Shape = house_body

roof_pts = [
    Vector(0, 0, 0),
    Vector(house_length, 0, 0),
    Vector(house_length / 2, 0, roof_height)
]
roof_face = Part.Face(Part.makePolygon(roof_pts + [roof_pts[0]]))
roof_shape = roof_face.extrude(Vector(0, house_width, 0))
roof_obj = doc.addObject("Part::Feature", "Roof")
roof_obj.Shape = roof_shape
roof_obj.Placement = App.Placement(Vector(0, 0, house_height), App.Rotation())

fused_shape = body_obj.Shape.fuse(roof_obj.Shape)
final_obj = doc.addObject("Part::Feature", "DemoHouse_Complete")
final_obj.Shape = fused_shape

body_obj.ViewObject.Visibility = False
roof_obj.ViewObject.Visibility = False

doc.recompute()
Gui.activeDocument().activeView().viewAxonometric()
Gui.SendMsgToActiveView("ViewFit")
