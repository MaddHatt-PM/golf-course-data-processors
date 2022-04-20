using UnityEngine;
using System.Collections;
using System.Collections.Generic;

// Info: All Mathf function use radians

public static class MathUtilities
{
    public static Vector3 CartesianToPolar(Vector3 point)
    {
        return new Vector3(
                Mathf.Sqrt(point.x * point.x + point.z * point.z),
                point.y,
                (Mathf.Approximately(0f, point.x)) ? 0f : Mathf.Atan(point.z / point.x));
    }

    // Polar Coordinate System: (r, y, θ)
    public static Vector3 PolarToCartesian(Vector3 input)
    {
        return new Vector3(
                input.x * Mathf.Cos(input.z),
                input.y,
                input.x * Mathf.Sin(input.z)
        );
    }
}