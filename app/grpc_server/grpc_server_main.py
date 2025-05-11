import asyncio
from concurrent import futures

import grpc

from grpc_server import notifications_pb2
from grpc_server.notifications_pb2_grpc import (
    NotificationServiceServicer,
    add_NotificationServiceServicer_to_server
)


class NotificationServicer(NotificationServiceServicer):
    async def SendNotification(self, request, context=None):
        """
        Send a notification via gRPC
        """
        try:
            # Log the notification
            print(
                f"GRPC NOTIFICATION: {request.title} "
                f"to user {request.recipient_id}"
            )
            print(f"Message: {request.message}")

            # Return success response
            return notifications_pb2.NotificationResponse(
                success=True,
                message="Notification sent successfully"
            )
        except Exception as e:
            # Return error response
            return notifications_pb2.NotificationResponse(
                success=False,
                notification_id="",
                message=f"Failed to send notification: {str(e)}"
            )


async def serve():
    """
    Start the gRPC server
    """
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    add_NotificationServiceServicer_to_server(
        NotificationServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    await server.start()
    print("gRPC server started on port 50051")
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(0)


def start_grpc_server():
    """Helper function to start the gRPC server"""
    asyncio.run(serve())


if __name__ == "__main__":
    start_grpc_server()
