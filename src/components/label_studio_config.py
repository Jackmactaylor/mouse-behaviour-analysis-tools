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
