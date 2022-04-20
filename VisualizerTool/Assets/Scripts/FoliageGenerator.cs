using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

[RequireComponent(typeof(MeshRenderer), typeof(MeshFilter))]
public class FoliageGenerator : MonoBehaviour
{
    [Title("Foliage Variables"), SerializeReference]
    public FoliageBase[] foliages = null;

    [Title("Debugging Variables")]
    public float profilePointSize = 0.25f;
    public Vector3 debugPoint;
    [Range(0, 50)] public int vertDrawLimit = 0;

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

    void OnDrawGizmos()
    {
        foreach (FoliageBase fol in foliages)
        {
            // Generate Mesh
            meshFilter.sharedMesh = fol.GenerateMesh(meshFilter.mesh);
            Vector3[] meshPoints = meshFilter.sharedMesh.vertices;

            Gizmos.matrix = transform.localToWorldMatrix;
            
            // // Generate Points
            // Gizmos.color = Color.red;
            // string pointsInfo = "";
            // int count = 1;
            // foreach (var point in meshPoints)
            // {
            //     Gizmos.DrawSphere(point, profilePointSize);
            //     pointsInfo += point.ToString() + " | ";

            //     if (count == vertDrawLimit)
            //         break;
            //     count++;
            // }

            // Generate Profile
            Vector3[] profilePoints = fol.GenerateProfile();
            Gizmos.color = Color.green;
            for (int i = 1; i < profilePoints.Length; i++)
            {
                Gizmos.DrawLine(profilePoints[i-1], profilePoints[i]);
            }
            foreach (var point in profilePoints)
            {
                Gizmos.DrawWireSphere(point, profilePointSize * 1.05f);
            }
        }

    }
}