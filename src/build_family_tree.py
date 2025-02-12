from typing import Optional

from graphviz import Digraph
import xml.etree.ElementTree as ET


class Person:
    def __init__(self, mothers: Optional[list] = [], fathers: Optional[list] = [], partners: Optional[list] = [],
                 children: Optional[list] = None, forename: Optional[str] = None, surname: Optional[str] = None,
                 id: Optional[str] = None,
                 role: Optional[str] = None):
        self.mothers = mothers
        self.fathers = fathers
        self.partners = partners
        self.children = children
        self.forename = forename
        self.surname = surname
        self.id = id
        self.role = role


xml_tree = ET.parse('../data/CFIB_GenealogyData_final.xml')

ns = {'': "http://www.tei-c.org/ns/1.0",
      'xml': "http://www.w3.org/XML/1998/namespace"
      }
root = xml_tree.getroot()

cfib_persons = root.findall(".//listPerson/person[@xml:id]", namespaces=ns)
i = 0


def build_family_tree(people_dict):
    """
    Build a family tree for a given person.

    :param person: Person object for whom the tree is being built.
    :param people_dict: Dictionary of all people, indexed by ID.
    """

    for person_key, person_val in people_dict.items():
        f = Digraph('neato', format='pdf', encoding='utf8', directory='family_trees',
                    filename=f'{person_key}_family_tree',
                    node_attr={'color': 'lightblue2', 'style': 'filled'}, strict=True)
        f.attr('node', shape='box')
        # todo: pass people_dict to be able to get people's names by dictionary lookup
        draw_all_relatives(f, person_key, person_val, set(), set(), set())

        if person_key == 'CFIB00169' or person_key == 'CFIB00245' or person_key == 'CFIB00762':
            f.view()
    # one_tree.render(filename=f'{cfib_person.id}_family_tree', directory='./family_trees', cleanup=True)


def draw_all_relatives(f, person_key, person_val, visited, nodes, graph_edges):
    if visited is None:
        visited = set()

    if person_key in visited:
        return
    if person_key not in nodes:
        f.node(person_key)
        nodes.add(person_key)

    visited.add(person_key)


    if person_val.partners:
        for partner_key in person_val.partners:
            if (person_key, partner_key) not in graph_edges and (partner_key, person_key) not in graph_edges:
                if partner_key not in nodes:
                    f.node(partner_key)
                    nodes.add(partner_key)
                f.edge(person_key, partner_key, label='', arrowhead="none", color="green")
                graph_edges.add((person_key, partner_key))
                graph_edges.add((partner_key, person_key))
                with f.subgraph() as sub:
                    sub.attr(rank="same")
                    sub.node(person_key)
                    sub.node(partner_key)
            draw_all_relatives(f, partner_key, flattened_people[partner_key], visited, nodes, graph_edges)
    if person_val.mothers:
        for mother_key in person_val.mothers:
            if (mother_key, person_key) not in graph_edges:
                if mother_key not in nodes:
                    f.node(mother_key)
                    nodes.add(mother_key)
                f.edge(mother_key, person_key, label='', color="green")
                graph_edges.add((mother_key, person_key))
            draw_all_relatives(f, mother_key, flattened_people[mother_key], visited, nodes, graph_edges)
    if person_val.fathers:
        for father_key in person_val.fathers:
            if (father_key, person_key) not in graph_edges:
                if father_key not in nodes:
                    f.node(father_key)
                    nodes.add(father_key)
                f.edge(father_key, person_key, label='', color="green")
                graph_edges.add((father_key, person_key))
            draw_all_relatives(f, father_key, flattened_people[father_key], visited, nodes, graph_edges)
    if person_val.children:
        for child_key in person_val.children:
            if (person_key, child_key) not in graph_edges:
                if child_key not in nodes:
                    f.node(child_key)
                    nodes.add(child_key)
                f.edge(person_key, child_key, label='', color="green")
                graph_edges.add((person_key, child_key))
            draw_all_relatives(f, child_key, flattened_people[child_key], visited, nodes, graph_edges)


def get_all_rels(cfib_person, people=[]):
    global current_person
    current_person = Person()
    current_person.forename = cfib_person.find('.//forename', namespaces=ns).text
    current_person.surname = cfib_person.find('.//surname', namespaces=ns).text
    current_person.role = cfib_person.find('.//roleName', namespaces=ns).text
    current_person.id = cfib_person.get('{http://www.w3.org/XML/1998/namespace}id')
    current_person.partners = []
    current_person.mothers = []
    current_person.fathers = []
    current_person.children = []
    people.append(current_person)
    # gets all relatives in the forward-direction
    all_relatives_forward = cfib_person.findall('.//persName[@type]', namespaces=ns)
    cfib_pers_fmt = f'#{current_person.id}'
    for relative in all_relatives_forward:
        current_person.partners = [rel.get('corresp').split('#')[1] for rel in
                                   relative.findall('[@type = "partner"]', namespaces=ns)]
        current_person.mothers = [rel.get('corresp').split('#')[1] for rel in
                                  relative.findall('[@type = "mother"]', namespaces=ns)]
        current_person.fathers = [rel.get('corresp').split('#')[1] for rel in
                                  relative.findall('[@type = "father"]', namespaces=ns)]
    all_matches_backward_root = root.findall(f'.//persName[@corresp = "{cfib_pers_fmt}"]', namespaces=ns)
    all_matches_backward_parents = root.findall(f'.//persName[@corresp = "{cfib_pers_fmt}"]...', namespaces=ns)
    matching_person_idx = None

    for i, one_match_backward_root in enumerate(all_matches_backward_root):
        # retrieve person from the people list based on ID,
        # make sure nobody is their own parent
        for person_idx, person in enumerate(people):
            if person.id == one_match_backward_root.attrib['corresp'].split('#')[1]:
                matching_person_idx = person_idx
        current_person = people[matching_person_idx]
        if one_match_backward_root.attrib['type'] == 'mother':
            mother_id = cfib_pers_fmt.split('#')[1]
            if mother_id not in current_person.mothers and mother_id != current_person.id:
                current_person.mothers.append(mother_id)
        if one_match_backward_root.attrib['type'] == 'father':
            father_id = cfib_pers_fmt.split('#')[1]
            if father_id not in current_person.fathers and father_id != current_person.id:
                current_person.fathers.append(father_id)
        if one_match_backward_root.attrib['type'] == 'partner':
            partner_id = all_matches_backward_parents[i].attrib['{http://www.w3.org/XML/1998/namespace}id']
            if partner_id not in current_person.partners:
                current_person.partners.append(partner_id)

    # Recurse into mothers, fathers, and partners if not already handled
    for mother_id in current_person.mothers:
        if not any(p.id == mother_id for p in people):
            mother_person = root.find(f'.//person[@xml:id="{mother_id}"]', namespaces=ns)
            get_all_rels(mother_person, people)
    for father_id in current_person.fathers:
        if not any(p.id == father_id for p in people):
            father_person = root.find(f'.//person[@xml:id="{father_id}"]', namespaces=ns)
            get_all_rels(father_person, people)
    for partner_id in current_person.partners:
        if not any(p.id == partner_id for p in people):
            partner_person = root.find(f'.//person[@xml:id="{partner_id}"]', namespaces=ns)
            get_all_rels(partner_person, people)

    return current_person, people


trees = {}

for cfib_person in cfib_persons:
    # todo: for each person object, search all relatives mother, father, and partners
    #  (search needs to happen in both directions, not just @type = partner but also @ corresp = person in question).
    # todo: Can I assume only one mother and father, or do I need to consider step-ness?
    # todo: for each leaf, recurse into searching and assigning mother, father, and partners until there are no more.
    # todo: try with the first ten people first.
    people = []

    current_person, people = get_all_rels(cfib_person, people)

    # current_person, people = get_all_children(cfib_person, people)
    # for person in people:
    #     for potential_child in people:
    #         if person.id in potential_child.mothers or person.id in potential_child.fathers:
    #             person.children.append(potential_child.id)

    trees.update({cfib_person.get('{http://www.w3.org/XML/1998/namespace}id'): people})

    # flatten and dedupe the trees
    flattened_people = {}

    for key, people_list in trees.items():

        for curr_person in people_list:
            canonical_partners = set()
            canonical_mothers = set()
            canonical_fathers = set()
            canonical_children = set()
            flattened_people[curr_person.id] = Person()
            for partner in curr_person.partners:
                canonical_partners.add(partner)
            for mother in curr_person.mothers:
                canonical_mothers.add(mother)
            for father in curr_person.fathers:
                canonical_fathers.add(father)
            for child in curr_person.children:
                canonical_children.add(child)
            flattened_people[curr_person.id].mothers = canonical_mothers
            flattened_people[curr_person.id].fathers = canonical_fathers
            flattened_people[curr_person.id].partners = canonical_partners
            flattened_people[curr_person.id].children = canonical_children

    for parent_key, parent_val in flattened_people.items():
        for child_key, child_val in flattened_people.items():
            if parent_key != child_key:
                for el in child_val.fathers:
                    if parent_key in el:
                        parent_val.children.add(child_key)
                for el in child_val.mothers:
                    if parent_key in el:
                        parent_val.children.add(child_key)

build_family_tree(flattened_people)

pass
