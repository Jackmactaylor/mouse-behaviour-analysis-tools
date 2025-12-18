"""
Label Studio XML Configuration for Mouse Behavior Analysis.
"""

LABEL_STUDIO_CONFIG = """
<View>
  <Video name="video" value="$video" sync="audio" frameRate="$fps" />
  <Labels name="label" toName="audio" choice="multiple">
    <Label value="Rubbing" background="red" hotkey="1"/>
    <Label value="Grooming" background="blue" hotkey="2"/>
    <Label value="Eating" background="green" hotkey="3"/>
  </Labels>
  <Audio name="audio" value="$video" sync="video" speed="false"/>
</View>
"""

PROJECT_TITLE = "Mouse Behavior Analysis"
