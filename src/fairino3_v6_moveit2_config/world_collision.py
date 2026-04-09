
import rclpy
from rclpy.node import Node
from moveit_msgs.msg import PlanningScene, CollisionObject
from geometry_msgs.msg import Pose, Point, Quaternion
from shape_msgs.msg import SolidPrimitive
from moveit_msgs.srv import ApplyPlanningScene

class AddCollisionObject(Node):
    def __init__(self):
        super().__init__('add_collision_object')

        self.client = self.create_client(ApplyPlanningScene, 'apply_planning_scene')

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting again...')

        self.get_logger().info('Service is available!')

        self.add_collision_object()

    def add_collision_object(self):
        planning_scene = PlanningScene()
        planning_scene.is_diff = True

        collision_object = CollisionObject()
        collision_object.id = "world_collision"
        collision_object.header.frame_id = "world"

        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [20.0, 20.0, 0.1]

        box_pose = Pose()
        box_pose.position = Point(x=0.0, y=0.0, z=-0.063)
        box_pose.orientation = Quaternion(w=1.0)

        collision_object.primitives.append(box)
        collision_object.primitive_poses.append(box_pose)
        collision_object.operation = CollisionObject.ADD

        planning_scene.world.collision_objects.append(collision_object)

        request = ApplyPlanningScene.Request()
        request.scene = planning_scene
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None:
            self.get_logger().info('Collision object added successfully!')
        else:
            self.get_logger().error('Failed to add collision object!')

def main(args=None):
    rclpy.init(args=args)
    node = AddCollisionObject()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()


