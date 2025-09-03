import { Hono } from "hono";
import { ApiResponse } from "../../shared/types";
import { getUserById, getActivitiesByDistance } from "../database/queries";

const discovery = new Hono();

// Calculate distance between two points using Haversine formula
function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 3959; // Earth's radius in miles
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

// Get personalized activity recommendations
discovery.get("/recommendations", async (c) => {
  try {
    const userId = c.req.header("X-User-ID");
    if (!userId) {
      return c.json<ApiResponse>({
        success: false,
        error: "Authentication required"
      }, 401);
    }

    const user = await getUserById(userId);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: "User not found"
      }, 404);
    }

    // Get nearby activities
    const activities = await getActivitiesByDistance(
      user.location.lat,
      user.location.lon,
      5 // 5 mile radius
    );

    // Filter and score activities based on user preferences
    const scoredActivities = activities
      .map(activity => {
        let score = 0;
        
        // Score based on activity preferences
        if (user.activityPreferences) {
          const activityType = activity.type;
          if (user.activityPreferences.includes(activityType)) {
            score += 3;
          }
        }

        // Score based on target audience match
        if (activity.targetAudience && user.kidsAges) {
          const hasMatchingAudience = activity.targetAudience.some(target => 
            user.kidsAges?.some(age => target.includes(age))
          );
          if (hasMatchingAudience) {
            score += 2;
          }
        }

        // Score based on social circle types
        if (user.socialCircleTypes?.includes('close_friends') && activity.type === 'private_outing') {
          score += 2;
        }
        if (user.socialCircleTypes?.includes('neighbors') && activity.type === 'open_door') {
          score += 2;
        }

        return {
          ...activity,
          score,
          matchReasons: [] // Could add specific reasons for the match
        };
      })
      .filter(activity => activity.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10); // Top 10 recommendations

    return c.json<ApiResponse>({
      success: true,
      data: { recommendations: scoredActivities }
    });

  } catch (error) {
    console.error("Error getting recommendations:", error);
    return c.json<ApiResponse>({
      success: false,
      error: "Internal server error"
    }, 500);
  }
});

// Discover users nearby
discovery.get("/users", async (c) => {
  try {
    const userId = c.req.header("X-User-ID");
    if (!userId) {
      return c.json<ApiResponse>({
        success: false,
        error: "Authentication required"
      }, 401);
    }

    const user = await getUserById(userId);
    if (!user) {
      return c.json<ApiResponse>({
        success: false,
        error: "User not found"
      }, 404);
    }

    const maxDistance = parseFloat(c.req.query("maxDistance") || "2");

    // Get nearby users (this would need a proper geospatial query in production)
    const result = await sqlite.execute(`
      SELECT userId, name, location_lat, location_lon, bio, kids_ages, 
             social_circle_types, activity_preferences
      FROM users_v2 
      WHERE userId != ?
    `, [userId]);

    const nearbyUsers = result.rows
      .map(row => {
        const distance = calculateDistance(
          user.location.lat,
          user.location.lon,
          row.location_lat as number,
          row.location_lon as number
        );

        if (distance <= maxDistance) {
          return {
            userId: row.userId,
            name: row.name,
            distance: Math.round(distance * 10) / 10, // Round to 1 decimal
            bio: row.bio,
            kidsAges: JSON.parse(row.kids_ages as string || '[]'),
            socialCircleTypes: JSON.parse(row.social_circle_types as string || '[]'),
            activityPreferences: JSON.parse(row.activity_preferences as string || '[]')
          };
        }
        return null;
      })
      .filter(Boolean)
      .sort((a, b) => a!.distance - b!.distance);

    return c.json<ApiResponse>({
      success: true,
      data: { users: nearbyUsers }
    });

  } catch (error) {
    console.error("Error discovering users:", error);
    return c.json<ApiResponse>({
      success: false,
      error: "Internal server error"
    }, 500);
  }
});

export default discovery;