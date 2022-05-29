from TerrainEditor import TerrainEditor, loaded_asset

app = TerrainEditor(target=loaded_asset(savename="Demo")).define_root()
app.mainloop()