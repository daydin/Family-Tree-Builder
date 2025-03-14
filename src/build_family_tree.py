from typing import Optional
from graphviz import Digraph
from lxml import etree

import argparse


class Person:
    def __init__(self, mothers: Optional[list] = [], fathers: Optional[list] = [], partners: Optional[list] = [],
                 children: Optional[list] = None, gender: Optional[str] = None, forename: Optional[str] = None,
                 surname: Optional[str] = None,
                 id: Optional[str] = None, role: Optional[str] = None, date_of_birth: Optional[str] = None,
                 date_of_death: Optional[str] = None):
        self.mothers = mothers
        self.fathers = fathers
        self.partners = partners
        self.children = children
        self.gender = gender
        self.forename = forename
        self.surname = surname
        self.id = id
        self.role = role
        self.date_of_birth = date_of_birth
        self.date_of_death = date_of_death


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", help="enter the path to the XML you want parsed")
parser.add_argument("-np", "--no-partners", action=argparse.BooleanOptionalAction,
                    help="use this flag if you want to omit drawing the partner links")
args = parser.parse_args()

xml_tree = etree.parse(args.filename)

ns = {'': "http://www.tei-c.org/ns/1.0",
      'xml': "http://www.w3.org/XML/1998/namespace"
      }
root = xml_tree.getroot()

cfib_persons = root.findall(".//listPerson/person[@xml:id]", namespaces=ns)
i = 0

people_dict = {}

colours = {'M': 'darkolivegreen2', 'W': 'cadetblue1', 'NB': 'darkorange2'}


def build_family_tree():
    """
    Build a family tree for a given person.

    :param person: Person object for whom the tree is being built.
    :param people_dict: Dictionary of all people, indexed by ID.
    """

    for person_key, person_val in people_dict.items():
        f = Digraph('neato', format='pdf', encoding='utf8', directory='family_trees',
                    filename=f'{person_key}_family_tree_NEW',
                    node_attr={'color': 'lightblue2', 'style': 'filled'}, strict=True)
        f.attr('node', shape='box')
        f.attr(newrank="true")
        f.attr(concentrate="true")
        # if person_key == 'CFIB00169' or person_key == 'CFIB00245' or person_key == 'CFIB00762':
        # if person_key == 'CFIB00687':
        draw_all_relatives(f, person_key, person_val, set(), set(), set(), {}, person_key)
        # f.view()
        f.render(filename=f'{person_key}_family_tree', directory='./family_trees', cleanup=True)


def draw_all_relatives(f, person_key, person_val, visited, nodes, graph_edges, generation_map, main_person_id):
    if visited is None:
        visited = set()

    if person_key in visited:
        return
    if person_key not in nodes:
        label, _ = create_label(main_person_id, person_key)
        f.node(person_key, label=f"{label}", color='red')
        nodes.add(person_key)

    visited.add(person_key)
    generation = generation_map.get(person_key, 0)

    if person_key not in generation_map:
        generation_map[person_key] = generation
    person = people_dict[person_key]
    if not args.no_partners:
        if person_val.partners:
            for partner_key in person_val.partners:
                if (person_key, partner_key) not in graph_edges and (partner_key, person_key) not in graph_edges:
                    create_node(f, main_person_id, nodes, partner_key)

                    with f.subgraph(name=f'cluster_{generation}') as sub:
                        f.edge(person_key, partner_key, label='', arrowhead="none", color="black")
                        graph_edges.add((person_key, partner_key))
                        graph_edges.add((partner_key, person_key))
                        sub.attr(rank="same")
                        sub.attr(style="invis")
                        if person_key != main_person_id:
                            node_colour = colours[person.gender]
                        else:
                            node_colour = 'red'
                        sub.node(person_key, color=node_colour)
                        if partner_key != main_person_id:
                            node_colour = colours[people_dict[partner_key].gender]
                        else:
                            node_colour = 'red'
                        sub.node(partner_key, color=node_colour)
                generation_map[partner_key] = generation
                draw_all_relatives(f, partner_key, people_dict[partner_key], visited, nodes, graph_edges,
                                   generation_map,
                                   main_person_id)
    if person_val.mothers and person_val.fathers:
        for mother_key in person_val.mothers:
            for father_key in person_val.fathers:
                parentage_key = f'parentage_{mother_key}_{father_key}'
                if (mother_key, parentage_key) not in graph_edges and (father_key, person_key) not in graph_edges:
                    create_node(f, main_person_id, nodes, mother_key)
                    create_node(f, main_person_id, nodes, father_key)

                    f.node(parentage_key, label='', shape='ellipse', width='0.2', height='0.2')
                    nodes.add(parentage_key)

                    f.edge(mother_key, parentage_key, label='', color="green")
                    graph_edges.add((mother_key, parentage_key))
                    graph_edges.add((mother_key, person_key))

                    f.edge(father_key, parentage_key, label='', color="green")
                    graph_edges.add((father_key, parentage_key))
                    graph_edges.add((father_key, person_key))
                    f.edge(parentage_key, person_key, label='', color="green")

                    graph_edges.add((parentage_key, person_key))


                else:
                    f.edge(parentage_key, person_key, label='', color="green")
                    graph_edges.add((parentage_key, person_key))

                if mother_key not in generation_map:
                    generation_map[mother_key] = generation - 1
                if father_key not in generation_map:
                    generation_map[father_key] = generation - 1

                with f.subgraph(name=f'cluster_{generation_map[person_key]}') as sub:
                    sub.attr(rank="same")
                    sub.attr(style="invis")
                    if person_key != main_person_id:
                        node_colour = colours[person.gender]
                    else:
                        node_colour = 'red'
                    sub.node(person_key, color=node_colour)

                draw_all_relatives(f, mother_key, people_dict[mother_key], visited, nodes, graph_edges, generation_map,
                                   main_person_id)
                draw_all_relatives(f, father_key, people_dict[father_key], visited, nodes, graph_edges, generation_map,
                                   main_person_id)

    else:
        if person_val.mothers and not person_val.fathers:
            for mother_key in person_val.mothers:
                if (mother_key, person_key) not in graph_edges:
                    create_node(f, main_person_id, nodes, mother_key)
                    f.edge(mother_key, person_key, label='', color="green")
                    graph_edges.add((mother_key, person_key))
                if mother_key not in generation_map:
                    generation_map[mother_key] = generation - 1

                with f.subgraph(name=f'cluster_{generation_map[person_key]}') as sub:
                    sub.attr(rank="same")
                    sub.attr(style="invis")
                    if person_key != main_person_id:
                        node_colour = colours[person.gender]
                    else:
                        node_colour = 'red'
                    sub.node(person_key, color=node_colour)

                draw_all_relatives(f, mother_key, people_dict[mother_key], visited, nodes, graph_edges, generation_map,
                                   main_person_id)
        if person_val.fathers and not person_val.mothers:
            for father_key in person_val.fathers:
                if (father_key, person_key) not in graph_edges:
                    create_node(f, main_person_id, nodes, father_key)
                    f.edge(father_key, person_key, label='', color="green")
                    graph_edges.add((father_key, person_key))
                if father_key not in generation_map:
                    generation_map[father_key] = generation - 1

                with f.subgraph(name=f'cluster_{generation_map[person_key]}') as sub:
                    sub.attr(rank="same")
                    sub.attr(style="invis")
                    if person_key != main_person_id:
                        node_colour = colours[person.gender]
                    else:
                        node_colour = 'red'
                    sub.node(person_key, color=node_colour)

                draw_all_relatives(f, father_key, people_dict[father_key], visited, nodes, graph_edges, generation_map,
                                   main_person_id)

    if person_val.children:
        for child_key in person_val.children:
            if (person_key, child_key) not in graph_edges:
                create_node(f, main_person_id, nodes, child_key)
                if not person_val.partners:
                    f.edge(person_key, child_key, label='', color="green")
                    graph_edges.add((person_key, child_key))
            if child_key not in generation_map:
                generation_map[child_key] = generation + 1

            with f.subgraph(name=f'cluster_{generation_map[child_key]}') as sub:
                sub.attr(rank="same")
                sub.attr(style="invis")
                if child_key != main_person_id:
                    node_colour = colours[people_dict[child_key].gender]
                else:
                    node_colour = 'red'
                sub.node(child_key, color=node_colour)

            draw_all_relatives(f, child_key, people_dict[child_key], visited, nodes, graph_edges, generation_map,
                               main_person_id)


def create_node(f, main_person_id, nodes, curr_pers_key):
    if curr_pers_key not in nodes:
        label, node_colour = create_label(main_person_id, curr_pers_key)
        f.node(curr_pers_key, label=f"{label}", color=node_colour)
        nodes.add(curr_pers_key)


def create_label(main_person_id, curr_person_to_label):
    label = ''
    person = people_dict[curr_person_to_label]

    if person.forename:
        label += person.forename + ' '
    if person.surname:
        label += person.surname + ' '
    if person.date_of_birth:
        label += 'DOB: ' + person.date_of_birth + ' '
    if person.date_of_death:
        label += 'DOD: ' + person.date_of_death
    if curr_person_to_label != main_person_id:
        node_colour = colours[person.gender]
    else:
        node_colour = 'red'
    return label, node_colour


def get_all_rels(cfib_person, people=[]):
    global current_person
    current_person = Person()
    current_person.forename = cfib_person.find('.//forename', namespaces=ns).text
    current_person.surname = cfib_person.find('.//surname', namespaces=ns).text
    current_person.role = cfib_person.find('.//roleName', namespaces=ns).text
    current_person.id = cfib_person.get('{http://www.w3.org/XML/1998/namespace}id')
    current_person.gender = cfib_person.find('.//gender', namespaces=ns).attrib['value']
    birth_node = cfib_person.find('.//birth', namespaces=ns)
    death_node = cfib_person.find('.//death', namespaces=ns)
    if birth_node is not None:
        current_person.date_of_birth = birth_node.attrib['when']
    if death_node is not None:
        current_person.date_of_death = death_node.attrib['when']
    current_person.partners = []
    current_person.mothers = []
    current_person.fathers = []
    current_person.children = []
    people.append(current_person)
    # gets all relatives in the forward-direction
    all_relatives_forward = cfib_person.findall('.//persName[@type]', namespaces=ns)
    cfib_pers_fmt = f'#{current_person.id}'
    for relative in all_relatives_forward:
        current_person.partners += [rel.get('corresp').split('#')[1] for rel in
                                    relative.findall('[@type = "partner"]', namespaces=ns)]
        current_person.mothers += [rel.get('corresp').split('#')[1] for rel in
                                   relative.findall('[@type = "mother"]', namespaces=ns)]
        current_person.fathers += [rel.get('corresp').split('#')[1] for rel in
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
            if partner_id not in current_person.partners and partner_id != current_person.id:
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

    people = []

    current_person, people = get_all_rels(cfib_person, people)

    trees.update({cfib_person.get('{http://www.w3.org/XML/1998/namespace}id'): people})

    for key, people_list in trees.items():

        for curr_person in people_list:
            canonical_partners = set()
            canonical_mothers = set()
            canonical_fathers = set()
            canonical_children = set()
            people_dict[curr_person.id] = Person()
            for partner in curr_person.partners:
                canonical_partners.add(partner)
            for mother in curr_person.mothers:
                canonical_mothers.add(mother)
            for father in curr_person.fathers:
                canonical_fathers.add(father)
            for child in curr_person.children:
                canonical_children.add(child)
            people_dict[curr_person.id].forename = curr_person.forename
            people_dict[curr_person.id].surname = curr_person.surname
            people_dict[curr_person.id].role = curr_person.role
            people_dict[curr_person.id].mothers = canonical_mothers
            people_dict[curr_person.id].fathers = canonical_fathers
            people_dict[curr_person.id].partners = canonical_partners
            people_dict[curr_person.id].children = canonical_children
            people_dict[curr_person.id].gender = curr_person.gender
            people_dict[curr_person.id].date_of_birth = curr_person.date_of_birth
            people_dict[curr_person.id].date_of_death = curr_person.date_of_death

    for parent_key, parent_val in people_dict.items():
        for child_key, child_val in people_dict.items():
            if parent_key != child_key:
                if parent_key in child_val.fathers or parent_key in child_val.mothers:
                    parent_val.children.add(child_key)
                    if parent_val.gender == 'M' and parent_key not in child_val.fathers:
                        child_val.fathers.add(parent_key)
                    if parent_val.gender == 'W' and parent_key not in child_val.mothers:
                        child_val.mothers.add(parent_key)

build_family_tree()

pass
