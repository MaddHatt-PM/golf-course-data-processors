import os
from pathlib import Path
import shutil
import subprocess
import sys
from tkinter import filedialog
from tkinter.messagebox import askyesno

from asset_project import LocationPaths
from utilities import CornerID, CornerID_to_name

TERRAIN_MAT = "TerrainMat"

def export_model(target:LocationPaths, input_texture:Path=None, testMode=False, scaler=1.0) -> list[Path]:
    outputdir = filedialog.askdirectory(
        title='Select directory for export',
        mustexist=True
    )

    if outputdir == '':
        return

    '''
    OBJ -> 3D Mesh file
    Referenced through Blender 2.93.0 OBJ output
    File Format Spec: https://en.wikipedia.org/wiki/Wavefront_.obj_file
    File Format Spec: https://www.loc.gov/preservation/digital/formats/fdd/fdd000507.shtml
    '''
    obj_path = Path(outputdir) / (target.savename + "Data") / "Model"
    if (obj_path.exists() == False):
        obj_path.mkdir(parents=True, exist_ok=True)
    
    obj_path = obj_path / (target.savename + ".obj")
    output = []

    '''HEADER'''
    header = [
        '# Terrain Grabber OBJ File: \'\'',
        '# https://github.com/MaddHatt-PM/golf-course-data-processors',
        'mtllib ' + target.savename + ".mtl",
        'o Terrain' # Mesh name
    ]
    output.append(header)

    '''VERTS'''
    verts = [
        '# v: (x,y,z) Vertices',
    ]

    xOffsets,yOffsets,elevs = [],[],[]
    with target.elevationCSV_path.open('r') as file:
        lines = file.read().splitlines()
        headers = lines.pop(0).split(',')
    
    xOffsetID = headers.index('offset-x')
    yOffsetID = headers.index('offset-y')
    elevID = headers.index('elevation')

    for ln in lines:
        raw = ln.split(',')
        pt = [eval(pt) for pt in raw]
        xOffsets.append(pt[xOffsetID])
        yOffsets.append(pt[yOffsetID])
        elevs.append(pt[elevID])

    minHeight = min(elevs)
    xOffsets = [pt * scaler for pt in xOffsets]
    yOffsets = [pt * scaler for pt in yOffsets]
    elevs = [(pt - minHeight) * scaler for pt in elevs]
    for i in range(len(xOffsets)):
        verts.append('v {} {} {}'.format(
            xOffsets[i],
            elevs[i],
            yOffsets[i],
        ))

    output.append(verts)

    '''UVS'''
    uvs = [
        '# vt: (u, v) texture coordinates, also called UVs'
    ]
    minXOffset, maxXOffset = min(xOffsets), max(xOffsets)
    minYOffset, maxYOffset = min(yOffsets), max(yOffsets)
    for i in range(len(xOffsets)):
        uvs.append('vt {:.6f} {:.6f}'.format(
            round(1- (xOffsets[i]-minXOffset)/(maxXOffset-minXOffset), ndigits=6),
            round(1- (yOffsets[i]-minYOffset)/(maxYOffset-minYOffset), ndigits=6)
        ))
    output.append(uvs)

    print(len(xOffsets))

    '''NORMALS'''
    normals = [
        '# vn: (x,y,z) vertex normal (typically between -1.0 to +1.0)',
        'vn 0.0000 1.0000 0.0000'
    ]
    output.append(normals)

    '''FACES (as tris)'''
    def count_repeats(iter:list[float]) -> int:
        '''Only works on aligned grids'''
        count = 1
        target = iter[0]
        threshold = 0.001
        while count < len(iter):
            if abs(target - iter[count]) <= threshold:
                count += 1
            else: break
        return count

    def count_until_reset(iter:list[float]) -> int:
        count = 1
        curr = iter[0]
        threshold = 0.001
        while count < (len(iter) - 1):
            if curr < iter[count]:
                curr = iter[count]
                count += 1
            else: break
        return count

    # vertCt_in_row = count_repeats(xOffsets)
    vertCt_in_col = count_until_reset(yOffsets)
    vertCt_in_row = len(xOffsets) // vertCt_in_col
    # vertCt_in_col = len(yOffsets) // vertCt_in_row
    print(vertCt_in_row, xOffsets[5])
    print(vertCt_in_col, yOffsets[5])

    faces = [
        'usemtl ' + TERRAIN_MAT,
        's 1',
        '# Counterclockwise Winding Order',
        '# Indexing starts at 1'
        '#   TriA: top-left bottom-left bottom-right',
        '#   TriB: top-left bottom-right top-right',
        '# f: (vertexIndex, uvIndex, uvIndex) faces in quad style',
    ]

    for rowID in range(1, vertCt_in_row):
        for colID in range(1, vertCt_in_col):
            pt_tl = '{}/{}/{}'.format(
                colID + (rowID-1)*vertCt_in_col,
                colID + (rowID-1)*vertCt_in_col,
                1)
            pt_bl = '{}/{}/{}'.format(
                colID+1 + (rowID-1)*vertCt_in_col, 
                colID+1 + (rowID-1)*vertCt_in_col, 
                1)
            pt_tr = '{}/{}/{}'.format(
                colID + rowID*vertCt_in_col,
                colID + rowID*vertCt_in_col,
                1)
            pt_br = '{}/{}/{}'.format(
                colID+1 + rowID*vertCt_in_col,
                colID+1 + rowID*vertCt_in_col,
                1)

            faces.append('f {} {} {}'.format(pt_tl, pt_bl, pt_br))
            faces.append('f {} {} {}'.format(pt_tl, pt_br, pt_tr))
            # break
        # break

    output.append(faces)

    '''TEXTURE'''
    if (input_texture is not None):
        texture_file = Path(target.savename + "_diff.png")
        texture_path = Path(outputdir) / (target.savename + "Data") / "Model" / str(texture_file)
        shutil.copy(input_texture, texture_path)
    
    with obj_path.open('w') as file:
        for section in output:
            file.write('\n'.join(section))
            file.write('\n')

    '''
    MTL -> Material Info File
    File Format Spec: https://www.loc.gov/preservation/digital/formats/fdd/fdd000508.shtml
    '''
    mtl_path = Path(outputdir) / (target.savename + "Data") / "Model" / (target.savename + ".mtl")
    with mtl_path.open('w') as file:
        output = [
            '# Terrain Grabber File: \'None\'',
            '# Material Count: 1',
            '',
            'newmtl ' + TERRAIN_MAT,
            'Ns 225.000000 ', # Specular highlights  [0, 1000]
            'Ka 0.800000  0.800000  0.800000 ', # Ambient Color [0.0, 1.0]
            'Kd 0.800000  0.800000  0.800000 ', # Diffuse Color [0.0, 1.0]
            'Ks 0.055000  0.055000  0.055000 ', # Specular Color [0.0, 1.0]
            'd 1.000000', # Transparency [0.0,1.0]
            'illum 2', # Shading Model
        ]
        
        if (input_texture is not None):
            output.append('map_Kd ' + str(texture_file)) # Diffuse Texture

        file.write('\n'.join(output))

if __name__ == '__main__':
    target = LocationPaths('DemoCourse')
    export_model(target)