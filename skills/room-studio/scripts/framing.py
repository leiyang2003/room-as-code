"""Camera framing shared with native export; plain Python for predictable validation."""
import math


def room_camera(room_id,room):
    authored=room.get('camera')
    if authored:
        return authored['position'],authored['target'],20
    x,y=room['center']
    return ((x+(-.3 if room_id=='bathroom' else 1.48),
             y-(2.15 if room_id=='bathroom' else 1.82),1.7),
            (x-.25,y+.75,1.08),20)


def overview_camera(scene,aspect=1/.7):
    """Fit all layout outline corners in a perspective camera with a small margin."""
    outline=scene.get('layout',{}).get('outline')
    if not outline:
        outline=[(room['center'][0]+sx*room['size'][0]/2,
                  room['center'][1]+sy*room['size'][1]/2)
                 for room in scene['rooms'].values() for sx in (-1,1) for sy in (-1,1)]
    xs,ys=zip(*outline);x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys)
    height=max(r['size'][2] for r in scene['rooms'].values())
    target=((x0+x1)/2,(y0+y1)/2,height/3)
    direction=(1,-1.25,1.35)
    norm=math.sqrt(sum(v*v for v in direction));direction=tuple(v/norm for v in direction)
    right=(-direction[1],direction[0],0)
    norm=math.hypot(*right[:2]);right=tuple(v/norm for v in right)
    up=(-direction[2]*right[1],direction[2]*right[0],direction[0]*right[1]-direction[1]*right[0])
    lens=42;tan_x=36/(2*lens);tan_y=tan_x/aspect
    dot=lambda a,b:sum(x*y for x,y in zip(a,b))
    distance=1
    for x in (x0,x1):
        for y in (y0,y1):
            for z in (0,height):
                q=(x-target[0],y-target[1],z-target[2])
                distance=max(distance,dot(q,direction)+1.1*max(abs(dot(q,right))/tan_x,abs(dot(q,up))/tan_y))
    return tuple(target[i]+distance*direction[i] for i in range(3)),target,lens
