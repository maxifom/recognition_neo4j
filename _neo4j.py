import os

from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher
import face_recognition
import cv2
import numpy
from event import event
from py_essentials import simpleRandom as r
import time as _time


def GetGraph(host="bolt://localhost:7687", password="root"):
    return Graph(host, password=password)


# def AddArrayToGraph(arr, delete=0):
#     graph = GetGraph()
#     if delete != 0:
#         graph.delete_all()
#     tx = graph.begin()
#     a = Node("Array", name="Random array", arr=arr)
#     tx.create(a)
#     tx.commit()


def AddUnknownToGraph(face):
    graph = GetGraph()
    tx = graph.begin()
    t = int(_time.time()) - 10000
    name = "Unknown_" + r.randomString(16)
    unknown = Node("Person", name=name, face=face, last_walked=t)
    tx.create(unknown)
    tx.commit()
    return name


def GetAllFacesFromGraph():
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    faces = list(matcher.match("Person"))
    knownFaces = []
    knownNames = []
    for face in faces:
        knownNames.append(face['name'])
        knownFaces.append(numpy.array(face['face']))
    data = {"faces": knownFaces, "names": knownNames}
    return data


def GetKnownFacesFromGraph():
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    faces = list(matcher.match("Person"))
    knownFaces = []
    knownNames = []
    for face in faces:
        if "Unknown" not in face['name']:
            knownNames.append(face['name'])
            knownFaces.append(numpy.array(face['face']))
    data = {"faces": knownFaces, "names": knownNames}
    # if knownNames.count() == 0:
    #     data = {"faces": numpy.array([]), "names": numpy.array([])}
    return data


def GetUnknownFacesFromGraph():
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    faces = list(matcher.match("Person"))
    unknownFaces = []
    unknownNames = []
    for face in faces:
        if "Unknown" in face['name']:
            unknownNames.append(face['name'])
            unknownFaces.append(numpy.array(face['face']))
    data = {"faces": unknownFaces, "names": unknownNames}
    return data


def DeleteGraph():
    graph = GetGraph()
    graph.delete_all()


# Adds unknown faces on image to neo4j
def AddUnknownFace(image, method='hog'):
    # print("[INFO] Adding unknown faces...")
    unknown = []

    image = cv2.imread(image)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # detect the (x, y)-coordinates of the bounding boxes
    # corresponding to each face in the input image
    boxes = face_recognition.face_locations(rgb,
                                            model=method)

    encodings = face_recognition.face_encodings(rgb, boxes)
    names = []
    faces = GetKnownFacesFromGraph()
    for encoding in encodings:
        matches = face_recognition.compare_faces(faces["faces"], encoding)
        if True not in matches:
            unknown.append(encoding)
    for _encoding in unknown:
        AddUnknownToGraph(_encoding.tolist())


def AddNamedFace(image, new_name, method='hog'):
    # print("[INFO] Adding named face...")
    unknown = []
    image_file = image
    image = cv2.imread(image)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb,
                                            model=method)

    encodings = face_recognition.face_encodings(rgb, boxes)
    faces = GetAllFacesFromGraph()
    has_unknown = False
    for encoding in encodings:
        matches = face_recognition.compare_faces(faces["faces"], encoding)
        # face found in all faces from db
        if True in matches:
            matchedIndexes = [i for (i, b) in enumerate(matches) if b]
            counts = {}
            for i in matchedIndexes:
                if 'Unknown' in faces['names'][i]:
                    name = faces["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                    has_unknown = True
            if has_unknown:
                name = max(counts, key=counts.get)
                unknown.append(name)
                has_unknown = False
        # Face not found in all faces from db
        else:
            AddKnownFaceToGraph(new_name=new_name, face=encoding.tolist())

    # print(len(unknown))
    for old_name in unknown:
        AddKnownFaceToGraph(old_name, new_name)
    # DeleteImages(image)
    os.remove(image_file)

def DeleteImages(name):
    # open('./images/'+str(name)+'.exist', 'a').close()
    imagesToDelete = os.listdir('./images/')
    for image in imagesToDelete:
        if name in image and '.exist' not in image:
            os.remove('./images/' + image)
    # os.remove('./images/' + str(name) + '.exist')


def AddKnownFaceToGraph(old_name='old_name', new_name='new_name', face= [], deleteImages=0):
    graph = GetGraph()
    tx = graph.begin()
    t = int(_time.time()) - 10000
    matcher = NodeMatcher(graph)
    person = matcher.match("Person").where("_.name = '" + old_name + "'").first()
    if person:
        person['name'] = new_name
        if person['last_walked'] != t:
            person['last_walked'] = t
        tx.push(person)
    else:
        if face == []:
            tx.rollback()
            return 'Error'
        person = Node("Person", name=new_name, face=face, last_walked=t)
        tx.create(person)
    tx.commit()
    event.set()
    if deleteImages > 0:
        DeleteImages(old_name)
    return 'Success'


def GetFaceFromGraph(person_name='person_name'):
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    person = matcher.match("Person", name=person_name).first()
    if person:
        return person['face']
    else:
        return []


def AddWalksWhenRelathionship(person_name='person_name', person_face=[]):
    # if person_face == [] and person_name != 'person_name':
    #     person_face = GetFaceFromGraph(person_name)
    t = int(_time.time())
    graph = GetGraph()
    tx = graph.begin()
    matcher = NodeMatcher(graph)
    person = matcher.match("Person", name=person_name).first()
    # last_walked = t
    if not person:
        tx.rollback()
        return 0
        # person = Node("Person", name=person_name, face=person_face, last_walked=t)
        # tx.create(person)
    else:
        last_walked = person['last_walked']
    t1 = last_walked
    if t - t1 > 60:
        time = Node("Time", time=t)
        person_time = Relationship(person, "WALKS_WHEN", time)
        tx.create(person_time)
        person['last_walked'] = t
        tx.push(person)
    tx.commit()


def AddWalksWhenToNames(names=[]):
    for name in names:
        AddWalksWhenRelathionship(name)


def AddWalksWithRelathionshipInInterval(interval=5 * 60):
    t = int(_time.time())
    _t = t - interval
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    people = list(matcher.match("Person", last_walked__gte=_t, last_walked__lte=t))
    for p1 in people:
        for p2 in people:
            if p1['name'] != p2['name']:
                AddWalksWithRelathionship(p1['name'], p2['name'])


def AddWalksWithRelathionship(name1, name2):
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    rel_matcher = RelationshipMatcher(graph)
    tx = graph.begin()
    t = int(_time.time())
    person_1 = matcher.match("Person").where("_.name = '" + name1 + "'").first()
    person_2 = matcher.match("Person").where("_.name = '" + name2 + "'").first()
    walks_with = rel_matcher.match(nodes=[person_1, person_2], r_type="WALKS_WITH").first()
    walks_with_reverse = rel_matcher.match(nodes=[person_2, person_1], r_type="WALKS_WITH").first()
    # print(walks_with)
    # print(walks_with_reverse)
    if walks_with is None:
        walks_with = Relationship(person_1, "WALKS_WITH", person_2, weight=0, last_time=t)
        tx.create(walks_with)
    elif t - walks_with['last_time'] > 60:
        walks_with['weight'] += 1
        walks_with['last_time'] = t
        tx.push(walks_with)
    if walks_with_reverse is None:
        walks_with_reverse = Relationship(person_2, "WALKS_WITH", person_1, weight=0, last_time=t)
        tx.create(walks_with_reverse)
    elif t - walks_with_reverse['last_time'] > 60:
        walks_with_reverse['weight'] += 1
        walks_with_reverse['last_time'] = t
        tx.push(walks_with_reverse)
    tx.commit()


def UpdateWalksWhenAll():
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    tx = graph.begin()
    people = list(matcher.match("Person"))
    for p in people:
        p['last_walked'] = int(_time.time())
        tx.push(p)
    tx.commit()


def AddWalksWithRelathionshipInIntervalForNames(names=[], interval=5 * 60):
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    t = int(_time.time())
    _t = t - interval
    people = []
    people_under_time = list(matcher.match("Person", last_walked__gte=_t, last_walked__lte=t))
    for name in names:
        _p = matcher.match("Person").where("_.name = '" + name + "'").first()
        if _p:
            people.append(_p)
    for p in people:
        for p1 in people_under_time:
            if p['name'] != p1['name']:
                AddWalksWithRelathionship(p['name'], p1['name'])


def GetPeople():
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    people = list(matcher.match("Person"))
    return people


def GetPersonByName(name):
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    person = matcher.match("Person").where("_.name='" + name + "'").first()
    return person


def GetRelathionships(person):
    graph = GetGraph()
    nodes = []
    for rel in graph.match((person,), r_type="WALKS_WITH"):
        nodes.append(rel)
    return nodes


def DeleteFromGraph(name):
    graph = GetGraph()
    tx = graph.begin()
    matcher = NodeMatcher(graph)
    person = matcher.match("Person").where("_.name='" + name + "'").first()
    print(person)
    if person:
        rel_when = list(graph.match((person,), r_type='WALKS_WHEN'))
        rels = list(graph.match((person,)))
        for r in rels:
            print(r)
            tx.separate(r)
        for r in rel_when:
            tx.delete(r.end_node)
        tx.delete(person)
        tx.commit()
        event.set()
        DeleteImages(name)
        return 'Success'
    DeleteImages(name)
    return 'Error'


def FindNodesByName(name):
    graph = GetGraph()
    matcher = NodeMatcher(graph)
    people = list(matcher.match("Person", name__contains=name))
    return people


def FindNodesByPhoto(image, method='hog'):
    image = cv2.imread(image)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    names = []
    boxes = face_recognition.face_locations(rgb,
                                            model=method)
    encodings = face_recognition.face_encodings(rgb, boxes)
    faces = GetAllFacesFromGraph()
    for encoding in encodings:
        # attempt to match each face in the input image to our known
        # encodings
        matches = face_recognition.compare_faces(faces['faces'],
                                                 encoding)
        name = "Unknown"

        # check to see if we have found a match
        if True in matches:
            # find the indexes of all matched faces then initialize a
            # dictionary to count the total number of times each face
            # was matched
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}

            # loop over the matched indexes and maintain a count for
            # each recognized face face
            for i in matchedIdxs:
                name = faces["names"][i]
                counts[name] = counts.get(name, 0) + 1

            # determine the recognized face with the largest number of
            # votes (note: in the event of an unlikely tie Python will
            # select first entry in the dictionary)
            name = max(counts, key=counts.get)

        # update the list of names
        if name != 'Unknown':
            names.append(name)
    people = []
    for name in names:
        people.append(GetPersonByName(name))
    return people


def ExportToFile():
    file = str(int(_time.time())) + '.graphml'
    filename = os.path.dirname(os.path.realpath(__file__)) + '/export/' + file
    graph = GetGraph()
    tx = graph.begin()
    tx.evaluate('CALL apoc.export.graphml.query("MATCH (n:Person) OPTIONAL match (n)-[r:WALKS_WITH]-() RETURN n,r",'
                '"' + str(filename) + '",{useTypes:true})')
    tx.commit()
    return file
# if __name__ == '__main__':
#     # DeleteGraph()
#     # AddNamedFace('1.jpg', 'Max')
#     # AddWalksWhenRelathionship('Max')
#     # AddNamedFace('4.jpg', 'A')
#     # AddWalksWhenRelathionship('A')
#     # AddNamedFace('3.jpg', 'L')
#     # AddWalksWhenRelathionship('L')
#     # AddWalksWithRelathionshipInInterval()
#     # Add only for names on photo
#     # AddWalksWithRelathionshipInIntervalForNames(['Max'])
#     # UpdateWalksWhenAll()
#     pass
