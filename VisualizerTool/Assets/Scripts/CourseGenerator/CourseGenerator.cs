using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

[RequireComponent(typeof(MeshRenderer), typeof(MeshFilter))]
public class CourseGenerator : MonoBehaviour
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
}