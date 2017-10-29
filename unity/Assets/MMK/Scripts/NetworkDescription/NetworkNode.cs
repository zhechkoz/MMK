using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

namespace MMK.NetworkDescription
{
		public class NetworkNode : NetworkItem
		{
				public List<string> neighbourSegments { get; private set; }
				private List<NetworkLane> lanes = new List<NetworkLane> ();

				protected override void Awake ()
				{
						base.Awake ();
						neighbourSegments = new List<string> ();
				}

				override public NetworkLane GetLaneByID (string id)
				{
						return lanes.Find (lane => lane.id == id);
				}

				override public List<NetworkLane> GetAllLanes ()
				{
						return lanes;	
				}

				override public void DeserializeFromJSON (JSONNode nodeJSON)
				{
						this.id = nodeJSON ["id"];
						this.osmID = nodeJSON ["osm"].AsInt;
						this.hierarchy = nodeJSON ["hierarchy"];

						JSONArray jsonLanes = nodeJSON ["lanes"].AsArray;
						JSONArray jsonShapes = nodeJSON ["shapes"].AsArray;
						JSONArray jsonVertices = nodeJSON ["vertices"].AsArray;
						JSONArray jsonNeightbors = nodeJSON ["neighbourSegments"].AsArray;

						foreach (JSONNode jsonVertex in jsonVertices) {
								float x = jsonVertex ["x"].AsFloat;
								float y = jsonVertex ["y"].AsFloat;
								float z = jsonVertex ["z"].AsFloat;
								this.vertices.Add (new Vector3 (x, y, z));
						}

						foreach (JSONString neighbour in jsonNeightbors) {
								neighbourSegments.Add (neighbour);
						}
						
						foreach (JSONNode shapeJSON in jsonShapes.Children) {
								NetworkShape shape = NetworkShape.DeserializeFromJSON (shapeJSON); 
								this.shapes.Add (shape);
						}
						
						foreach (JSONNode laneJSON in jsonLanes.Children) {
								NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
								this.lanes.Add (lane);
						}
				}
		}
}
