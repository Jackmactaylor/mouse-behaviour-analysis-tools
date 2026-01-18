"""
Label Studio XML Configuration for Mouse Behavior Analysis.
"""

LABEL_STUDIO_CONFIG = """
<View>
  <Video name="video" value="$video" sync="audio" frameRate="$fps" defaultPlaybackSpeed="1.0" height="500" />
  <Labels name="label" toName="audio">
    <Label value="Rubbing" background="red" hotkey="1"/>
    <Label value="Grooming" background="blue" hotkey="2"/>
    <Label value="Eating" background="green" hotkey="3"/>
    <Label value="Active" background="#FFA500"/>
  </Labels>
  <Audio name="audio" value="$video" sync="video" speed="false" height="100"/>
</View>
"""

PROJECT_TITLE = "Mouse Behavior Analysis"
PROJECT_TITLE_MULTI = "Mouse Behavior Analysis (Multi-Mouse)"

LABEL_STUDIO_MULTI_CONFIG = """
<View>
  <Video name="video" value="$video" sync="audio" frameRate="$fps" defaultPlaybackSpeed="1.0" height="400" />
  <Audio name="audio" value="$audio" sync="video" speed="false" height="100" />
  
  <View style="display: flex; justify-content: space-around; padding: 10px; background: #f8f9fa; border-radius: 5px; margin-top: 10px;">
    <View style="flex: 1; padding: 0 10px; border-right: 1px solid #ddd; text-align: center;">
      <Header value="Mouse 1 (Left)" style="font-size: 1.1em; margin-bottom: 5px;" />
      <Labels name="m1_label" toName="audio">
        <Label value="Rubbing (M1)" background="#FF0000" hotkey="1"/>
        <Label value="Grooming (M1)" background="#0000FF" hotkey="q"/>
      </Labels>
    </View>

    <View style="flex: 1; padding: 0 10px; border-right: 1px solid #ddd; text-align: center;">
      <Header value="Mouse 2" style="font-size: 1.1em; margin-bottom: 5px;" />
      <Labels name="m2_label" toName="audio">
        <Label value="Rubbing (M2)" background="#AA0000" hotkey="2"/>
        <Label value="Grooming (M2)" background="#0000AA" hotkey="w"/>
      </Labels>
    </View>

    <View style="flex: 1; padding: 0 10px; border-right: 1px solid #ddd; text-align: center;">
      <Header value="Mouse 3" style="font-size: 1.1em; margin-bottom: 5px;" />
      <Labels name="m3_label" toName="audio">
        <Label value="Rubbing (M3)" background="#550000" hotkey="3"/>
        <Label value="Grooming (M3)" background="#000055" hotkey="e"/>
      </Labels>
    </View>

    <View style="flex: 1; padding: 0 10px; text-align: center;">
      <Header value="Mouse 4 (Right)" style="font-size: 1.1em; margin-bottom: 5px;" />
      <Labels name="m4_label" toName="audio">
        <Label value="Rubbing (M4)" background="#330000" hotkey="4"/>
        <Label value="Grooming (M4)" background="#000033" hotkey="r"/>
      </Labels>
    </View>
  </View>
</View>
"""
