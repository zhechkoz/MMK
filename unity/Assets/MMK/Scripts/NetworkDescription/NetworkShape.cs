using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkShape : MonoBehaviour {
		public string id;
		public List<Vector3> vertices = new List<Vector3> ();

		public static NetworkShape deserializeFromJSON(JSONNode shapeJSON)
		{
				NetworkShape shape = new NetworkShape ();
				shape.id = shapeJSON["ID"];
				JSONArray jsonVertices = shapeJSON ["vertices"].AsArray;
				foreach (JSONNode jsonVertex in jsonVertices) {
						float x = jsonVertex ["x"].AsFloat;
						float y = jsonVertex ["y"].AsFloat;
						float z = jsonVertex ["z"].AsFloat;
						shape.vertices.Add (new Vector3 (x, y, z));
				}
				return shape;
		}

		public List<Vector3> calculateAABB() {
				Vector3 max = new Vector3 (float.MinValue, float.MinValue, float.MinValue);
				Vector3 min = new Vector3 (float.MaxValue, float.MaxValue, float.MaxValue);
				foreach (Vector3 vertex in vertices) {
						max.x = Mathf.Max (max.x, vertex.x);
						max.y = Mathf.Max (max.y, vertex.y);
						max.z = Mathf.Max (max.z, vertex.z);
						min.x = Mathf.Min (min.x, vertex.x);
						min.y = Mathf.Min (min.y, vertex.y);
						min.z = Mathf.Min (min.z, vertex.z);
				}

				Vector3 d = new Vector3 (max.x - min.x, max.y - min.y, max.z - min.z);
				Vector3 center = new Vector3(min.x + d.x / 2.0f, min.y + d.y / 2.0f, min.z + d.z / 2.0f);

				return new List<Vector3> () { center, d }; 
		}
}
