using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

namespace MMK.NetworkDescription
{
		public abstract class NetworkItem : MonoBehaviour
		{
				public string id { get; protected set; }
				public int osmID { get; protected set; }
				public string hierarchy { get; protected set; }
				public List<Vector3> vertices { get; protected set; }
				public List<NetworkShape> shapes { get; protected set; }
				public abstract NetworkLane GetLaneByID (string id);
				public abstract List<NetworkLane> GetAllLanes ();
				public abstract void DeserializeFromJSON (JSONNode nodeJSON, Dictionary<string , NetworkLane> lanes);

				protected virtual void Awake ()
				{
						vertices = new List<Vector3> ();
						shapes = new List<NetworkShape> ();
				}

				public List<Vector3> GetBoxColliderSizeAndCenter ()
				{
						foreach (NetworkShape shape in shapes) {
								// Only the first shape represents roads
								if (shape.id.EndsWith (":0")) {
										return shape.CalculateExtendedAABB ();
								}
						}
						return null;
				}
		}
}
