import { Hono } from "hono";
import { BroadcastActivityRequest, ApiResponse, Activity } from "../../shared/types";
import { createActivity, getActivitiesByDistance } from "../database/queries";
import { v4 as uuidv4 } from "uuid";

const activities = new Hono();

activities.post("/", async (c) => {
  try {
    const body: BroadcastActivityRequest = await c.req.json();
    
    // Validate required fields
    if (!body.type || !body.title || !body.location || !body.targetAudience) {
      return c.json<ApiResponse>({
        success: false,
        error: "Missing required fields"
      }, 400);
    }

    // Get user ID from authentication (assuming it's in headers or context)
    const creatorId = c.req.header("X-User-ID");
    if (!creatorId) {
      return c.json<ApiResponse>({
        success: false,
        error: "Authentication required"
      }, 401);
    }

    const activity: Activity = {
      activityId: uuidv4(),
      creatorId,
      type: body.type,
      title: body.title,
      description: body.description,
      location: body.location,
      startTime: body.startTime,
      endTime: body.endTime,
      targetAudience: body.targetAudience,
      maxParticipants: body.maxParticipants,
      currentParticipants: 0,
      status: "active"
    };

    await createActivity(activity);

    return c.json<ApiResponse>({
      success: true,
      data: { activityId: activity.activityId }
    });

  } catch (error) {
    console.error("Error creating activity:", error);
    return c.json<ApiResponse>({
      success: false,
      error: "Internal server error"
    }, 500);
  }
});

activities.get("/nearby", async (c) => {
  try {
    const lat = parseFloat(c.req.query("lat") || "0");
    const lon = parseFloat(c.req.query("lon") || "0");
    const maxDistance = parseFloat(c.req.query("maxDistance") || "5");

    if (!lat || !lon) {
      return c.json<ApiResponse>({
        success: false,
        error: "Location coordinates required"
      }, 400);
    }

    const activities = await getActivitiesByDistance(lat, lon, maxDistance);

    return c.json<ApiResponse>({
      success: true,
      data: { activities }
    });

  } catch (error) {
    console.error("Error fetching nearby activities:", error);
    return c.json<ApiResponse>({
      success: false,
      error: "Internal server error"
    }, 500);
  }
});

export default activities;