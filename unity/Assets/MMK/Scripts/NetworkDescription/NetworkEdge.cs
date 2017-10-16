using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkEdge : NetworkItem
{
		string start;
		string end;
		double length;
		double maxSpeed;
		bool oneway;
		public List<NetworkLane> forwardLanes = new List<NetworkLane> ();
		public List<NetworkLane> backwardLanes = new List<NetworkLane> ();

		override public NetworkLane GetLaneByID (string id)
		{
				foreach (NetworkLane lane in forwardLanes) {
						if (lane.id == id) {
								return lane;
						}
				}

				foreach (NetworkLane lane in backwardLanes) {
						if (lane.id == id) {
								return lane;
						}
				}

				return null;
		}

		public static NetworkEdge DeserializeFromJSON (JSONNode segmentJSON)
		{
				NetworkEdge segment = new NetworkEdge ();
				segment.id = segmentJSON ["id"];
				segment.osmID = segmentJSON ["osm"].AsInt;
				segment.start = segmentJSON ["start"];
				segment.end = segmentJSON ["end"];
				segment.length = segmentJSON ["length"].AsDouble;
				segment.maxSpeed = segmentJSON ["maxspeed"].AsDouble;
				segment.hierarchy = segmentJSON ["hierarchy"];
				segment.oneway = segmentJSON ["oneway"] != null && segmentJSON ["oneway"].AsBool;
						
				JSONArray forward = segmentJSON ["lanes"] ["forward"].AsArray;
				JSONArray backward = segmentJSON ["lanes"] ["backward"].AsArray;
				JSONArray shapes = segmentJSON ["shapes"].AsArray;

				JSONArray jsonVertices = segmentJSON ["vertices"].AsArray;
				foreach (JSONNode jsonVertex in jsonVertices) {
						float x = jsonVertex ["x"].AsFloat;
						float y = jsonVertex ["y"].AsFloat;
						float z = jsonVertex ["z"].AsFloat;
						segment.vertices.Add (new Vector3 (x, y, z));
				}

				if (shapes != null && shapes.Count > 0) {
						foreach (JSONNode shapeJSON in shapes.Children) {
								NetworkShape shape = NetworkShape.DeserializeFromJSON (shapeJSON); 
								segment.shapes.Add (shape);
						}
				}

				if (forward != null && forward.Count > 0) {
						foreach (JSONNode laneJSON in forward.Children) {
								NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
								segment.forwardLanes.Add (lane);
						}
				}

				if (backward != null && backward.Count > 0) {
						foreach (JSONNode laneJSON in backward.Children) {
								NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
								segment.backwardLanes.Add (lane);
						}
				}
				return segment;
		}
	
}
