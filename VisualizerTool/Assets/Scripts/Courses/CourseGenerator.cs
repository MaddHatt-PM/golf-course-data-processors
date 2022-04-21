using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

[RequireComponent(typeof(MeshRenderer), typeof(MeshFilter))]
public class CourseGenerator : MonoBehaviour
{
    public TextAsset dataCSV;
    public TextAsset infoCSV;
    
    [Header("Debug Variables")]
    public float gizmo_vertSize = 0.25f;
    public bool autorefresh = false;

    private MeshRenderer _meshRenderer;
    public MeshRenderer meshRenderer
    {
        get
        {
            if (_meshRenderer == null) _meshRenderer = GetComponent<MeshRenderer>();
            return _meshRenderer;
        }
        set => _meshRenderer = value;
    }

    private MeshFilter _meshFilter;
    public MeshFilter meshFilter
    {
        get
        {
            if (_meshFilter == null) _meshFilter = GetComponent<MeshFilter>();
            return _meshFilter;
        }
        set => _meshFilter = value;
    }

    void OnValidate()
    {

    }

    void OnDrawGizmos()
    {
        if (autorefresh == true) Generate();

        Vector3[] meshPoints = meshFilter.sharedMesh.vertices;
        Gizmos.matrix = transform.localToWorldMatrix;

        // Generate Points
        Gizmos.color = Color.red;
        int count = 1;
        foreach (var point in meshPoints)
        {
            Gizmos.DrawSphere(point, gizmo_vertSize);
            count++;
        }
    }

    [Button("Generate")]
    public void Generate()
    {
        Mesh mesh = new Mesh();
        if (mesh == null) mesh = new Mesh();
        mesh.Clear();

        List<Vector3> verts = new List<Vector3>();
        List<int> tris = new List<int>();

        string[] vertStrs = dataCSV.text.Split('\n');
        for (int i = 1; i < vertStrs.Length - 1; i++)
        {
            string[] vertPts = vertStrs[i].Split(',');
            Vector3 vert = new Vector3(
                float.Parse(vertPts[0]),
                float.Parse(vertPts[1]),
                float.Parse(vertPts[2])
            );

            verts.Add(vert);
        }

        // Retrieve dimensions 
        string[] sizeStrs = infoCSV.text.Split('\n')[1].Split(',');
        int xLength = int.Parse(sizeStrs[0]);
        int yLength = int.Parse(sizeStrs[1]);

        // Triangulation

        // Finalize mesh
        mesh.vertices = verts.ToArray();
        mesh.triangles = tris.ToArray();
        // mesh.RecalculateNormals();
        meshFilter.sharedMesh = mesh;
    }
}