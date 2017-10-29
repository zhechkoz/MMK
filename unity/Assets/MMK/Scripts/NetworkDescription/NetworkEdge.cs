using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkEdge : NetworkItem
{
		public string start { get; private set; }
		public string end { get; private set; }
		public double length { get; private set; }
		public double maxSpeed { get; private set; }
		public bool oneway { get; private set; }
		public List<NetworkLane> forwardLanes { get; private set; }
		public List<NetworkLane> backwardLanes { get; private set; }

		protected override void Awake()
		{
				base.Awake ();
				forwardLanes = new List<NetworkLane> ();
				backwardLanes = new List<NetworkLane> ();
		}

		override public NetworkLane GetLaneByID (string id)
		{
				NetworkLane searchedLane = forwardLanes.Find(lane => lane.id == id);
				if (searchedLane == null) {
						searchedLane = backwardLanes.Find(lane => lane.id == id);
				}

				return searchedLane;
		}

		override public List<NetworkLane> GetAllLanes () {
				var allLanes = new List<NetworkLane> ();
				allLanes.AddRange(forwardLanes);
				allLanes.AddRange (backwardLanes);

				return allLanes;
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
						
				foreach (JSONNode shapeJSON in jsonShapes.Children) {
						NetworkShape shape = NetworkShape.DeserializeFromJSON (shapeJSON); 
						this.shapes.Add (shape);
				}
						
				foreach (JSONNode laneJSON in jsonForward.Children) {
						NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
						this.forwardLanes.Add (lane);
				}
						
				foreach (JSONNode laneJSON in jsonBackward.Children) {
						NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
						this.backwardLanes.Add (lane);
				}
		}
}
