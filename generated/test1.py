import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Vector
import Part

BODY_LENGTH = 200.0
BODY_WIDTH = 80.0
BODY_HEIGHT = 50.0
WHEEL_RADIUS = 30.0
WHEEL_THICKNESS = 15.0
WHEEL_OFFSET = 40.0

def createToyCar():
    doc = App.newDocument("ToyCar")

    body_shape = Part.makeBox(BODY_LENGTH, BODY_WIDTH, BODY_HEIGHT, Vector(0, 0, WHEEL_RADIUS))
    body_obj = doc.addObject("Part::Feature", "CarBody")
    body_obj.Shape = body_shape

    wheel_positions = [
        Vector(WHEEL_OFFSET, -WHEEL_THICKNESS/2, WHEEL_RADIUS),
        Vector(WHEEL_OFFSET, BODY_WIDTH + WHEEL_THICKNESS/2, WHEEL_RADIUS),
        Vector(BODY_LENGTH - WHEEL_OFFSET, -WHEEL_THICKNESS/2, WHEEL_RADIUS),
        Vector(BODY_LENGTH - WHEEL_OFFSET, BODY_WIDTH + WHEEL_THICKNESS/2, WHEEL_RADIUS)
    ]

    wheel_objs = []
    for i, pos in enumerate(wheel_positions):
        wheel_shape = Part.makeCylinder(WHEEL_RADIUS, WHEEL_THICKNESS, pos, Vector(0, 1, 0))
        wheel_obj = doc.addObject("Part::Feature", f"Wheel_{i+1}")
        wheel_obj.Shape = wheel_shape
        wheel_objs.append(wheel_obj)

    fused_shape = body_obj.Shape
    for wheel in wheel_objs:
        fused_shape = fused_shape.fuse(wheel.Shape)

    final_obj = doc.addObject("Part::Feature", "ToyCar_Complete")
    final_obj.Shape = fused_shape

    body_obj.ViewObject.Visibility = False
    for wheel in wheel_objs:
        wheel.ViewObject.Visibility = False

    doc.recompute()
    Gui.activeDocument().activeView().viewAxometric()
    Gui.SendMsgToActiveView("ViewFit")

    return doc

if __name__ == "__main__":
    createToyCar()
