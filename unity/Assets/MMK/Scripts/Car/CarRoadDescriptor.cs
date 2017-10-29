using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace MMK.Car
{
		public class CarRoadDescriptor : MonoBehaviour
		{
				private Dictionary<string, NetworkItem> currentRoads = new Dictionary<string, NetworkItem> ();

				private string id, lastId;
				private NetworkItem networkItem;

				bool beenThere = true;
				NetworkDescription desc;

				void Start() {
						desc = GameObject.Find("tum_0").GetComponent<NetworkDescription>();
				}

				void Update ()
				{
						CurrentRoadInformation (out id, out networkItem);
						//Debug.Log (id);

						if (beenThere) {
								desc.CalculateRoute (":2285938307_0_0", "-155040996_0");
								beenThere = false;
						}
				}

				public void CurrentRoadInformation (out string laneID, out NetworkItem networkItem)
				{
						var currentPosition = MMKExtensions.ToVector2(this.transform.position);
						float minimalDistance = float.MaxValue;
						networkItem = null;
						laneID = null;

						foreach (NetworkItem item in currentRoads.Values) {
								foreach (NetworkLane lane in item.GetAllLanes ()) {
										List<Vector3> vertices = lane.vertices;
										for (int i = 0; i < vertices.Count - 1; i++) {
												var laneA = MMKExtensions.ToVector2 (vertices [i]);
												var laneB = MMKExtensions.ToVector2 (vertices [i + 1]);
												float currentDistance = MMKExtensions.DistanceLineToPoint (laneA, laneB, currentPosition, true);
												if (currentDistance < minimalDistance) {
														minimalDistance = currentDistance;
														laneID = lane.id;
														networkItem = item;
												}
										}
								}
						}
				}

				void OnTriggerEnter (Collider other)
				{
						GameObject networkElement = other.gameObject;
						string id = networkElement.name;
						NetworkItem item = networkElement.GetComponent<NetworkItem> ();
						if (item != null && !currentRoads.ContainsKey (id)) {
								currentRoads.Add (id, item);
						}
				}

				void OnTriggerExit (Collider other)
				{
						string id = other.gameObject.name;
						if (currentRoads.ContainsKey (id)) {
								currentRoads.Remove (id);
						}
				}
		}
}
