using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkEdge : NetworkItem
{
		public string start;
		public string end;
		public double length;
		public double maxSpeed;
		public bool oneway;
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

		override public void DeserializeFromJSON (JSONNode segmentJSON)
		{
				this.id = segmentJSON ["id"];
				this.osmID = segmentJSON ["osm"].AsInt;
				this.start = segmentJSON ["start"];
				this.end = segmentJSON ["end"];
				this.length = segmentJSON ["length"].AsDouble;
				this.maxSpeed = segmentJSON ["maxspeed"].AsDouble;
				this.hierarchy = segmentJSON ["hierarchy"];
				this.oneway = segmentJSON ["oneway"] != null && segmentJSON ["oneway"].AsBool;
						
				JSONArray jsonForward = segmentJSON ["lanes"] ["forward"].AsArray;
				JSONArray jsonBackward = segmentJSON ["lanes"] ["backward"].AsArray;
				JSONArray jsonShapes = segmentJSON ["shapes"].AsArray;
				JSONArray jsonVertices = segmentJSON ["vertices"].AsArray;

				foreach (JSONNode jsonVertex in jsonVertices) {
						float x = jsonVertex ["x"].AsFloat;
						float y = jsonVertex ["y"].AsFloat;
						float z = jsonVertex ["z"].AsFloat;
						vertices.Add (new Vector3 (x, y, z));
				}

				if (jsonShapes != null) {
						foreach (JSONNode shapeJSON in jsonShapes.Children) {
								NetworkShape shape = NetworkShape.DeserializeFromJSON (shapeJSON); 
								this.shapes.Add (shape);
						}
				}

				if (jsonForward != null) {
						foreach (JSONNode laneJSON in jsonForward.Children) {
								NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
								this.forwardLanes.Add (lane);
						}
				}

				if (jsonBackward != null) {
						foreach (JSONNode laneJSON in jsonBackward.Children) {
								NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
								this.backwardLanes.Add (lane);
						}
				}
		}
	
}
