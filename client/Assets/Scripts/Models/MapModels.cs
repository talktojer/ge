using System;

namespace GalacticEmpire.Models
{
    /// <summary>
    /// Data models for Map API responses
    /// Contract: docs/PHASE_C2A_MAP_API.md (PR #15)
    /// </summary>

    [Serializable]
    public class GalaxyOverviewResponse
    {
        public string shard_id;
        public int width;
        public int height;
        public SectorStub[] sectors;
    }

    [Serializable]
    public class SectorStub
    {
        public int id;
        public int x;
        public int y;
        public string name;
        public string sector_type;
        public int planet_count;
        public int ship_count;
    }

    [Serializable]
    public class SectorDetailResponse
    {
        public int id;
        public int x;
        public int y;
        public string name;
        public string sector_type;
        public int planet_count;
        public PlanetData[] planets;
        public ShipData[] ships;
    }

    [Serializable]
    public class PlanetData
    {
        public int id;
        public string name;
        public string owner_id;
        public string owner_name;
        public bool is_safe_harbor;
    }

    [Serializable]
    public class ShipData
    {
        public int id;
        public string owner_id;
        public string owner_name;
        public string class_type;
        public float position_x;
        public float position_y;
        public bool is_docked;
        public float heading;
        public float speed;
    }

    [Serializable]
    public class WSMessage
    {
        public string type;
    }

    [Serializable]
    public class WSAuthMessage : WSMessage
    {
        public string token;
    }

    [Serializable]
    public class WSSubscribeMessage : WSMessage
    {
        public int sector_id;
    }

    [Serializable]
    public class WSAuthenticatedMessage : WSMessage
    {
        public string player_id;
    }

    [Serializable]
    public class WSSubscribedMessage : WSMessage
    {
        public int sector_id;
    }

    [Serializable]
    public class WSSectorSnapshotMessage : WSMessage
    {
        public int sector_id;
        public string timestamp;
        public SectorSnapshotData data;
    }

    [Serializable]
    public class SectorSnapshotData
    {
        public int id;
        public int x;
        public int y;
        public ShipData[] ships;
        public PlanetData[] planets;
    }

    [Serializable]
    public class WSSectorDeltaMessage : WSMessage
    {
        public int sector_id;
        public int tick;
        public string timestamp;
        public SectorEvent[] events;
    }

    [Serializable]
    public class SectorEvent
    {
        public string event_type;
        public string message;
        public int ship_id;
        public Position old_position;
        public Position new_position;
        public float heading;
        public float speed;
    }

    [Serializable]
    public class Position
    {
        public float x;
        public float y;
    }

    [Serializable]
    public class WSErrorMessage : WSMessage
    {
        public string message;
    }
}
