using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[ExecuteAlways]
public class Golfball : MonoBehaviour
{
    public Material insideMat;
    public Material outsideMat;

    void Update()
    {
        FoliageGenerator[] generators = Object.FindObjectsOfType<FoliageGenerator>();

        foreach (FoliageGenerator gen in generators)
        {
            MeshRenderer meshRenderer = gen.GetComponent<MeshRenderer>();
            bool isInCollider = false;
            foreach (FoliageBase foliage in gen.foliages)
            {
                isInCollider = foliage.IsInCollider(transform.position - gen.transform.position);
                if (isInCollider) break;
            }

            meshRenderer.sharedMaterial = (isInCollider) ? insideMat : outsideMat;
        }
    }
}
