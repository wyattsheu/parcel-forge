"""Explicit connected-component policy; never silently discard modeled parts."""
def face_components(faces, vertex_count):
 parents=list(range(vertex_count))
 def find(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for face in faces:
  for i in face[1:]:parents[find(int(i))]=find(int(face[0]))
 groups={}
 for index,face in enumerate(faces):groups.setdefault(find(int(face[0])),[]).append(index)
 return sorted(groups.values(),key=len,reverse=True)

def srgb_to_linear(value):
 if not 0<=value<=1:raise ValueError('expected normalized sRGB')
 return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4
