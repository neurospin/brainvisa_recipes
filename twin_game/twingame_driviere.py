#!/usr/bin/env python

import anatomist.api as ana
from soma.qt_gui.qt_backend import Qt
from soma.aims import lazy_read_data
import json
import os
import os.path as osp
import numpy as np
import argparse


# fix PreloadIterator in aims < 5.2
if not hasattr(lazy_read_data.PreloadIterator, '__next__'):
    lazy_read_data.PreloadIterator.__next__ \
        = lazy_read_data.PreloadIterator.next
    lazy_read_data.LazyReadData.get_data \
        = lazy_read_data.LazyReadData._lazy_read_


class DragFrame(Qt.QLabel):

    def mouseMoveEvent(self, e):

        if e.buttons() == Qt.Qt.LeftButton:
            drag = Qt.QDrag(self)
            mime = Qt.QMimeData()
            drag.setMimeData(mime)

            parent = self.parent()
            pixmap = Qt.QPixmap(parent.size())
            parent.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.Qt.MoveAction)


class TwinGame(Qt.QMainWindow):

    colors_list = [
        (182, 0, 0),
        (78, 182, 68),
        (39, 53, 242),
        (237, 255, 114),
        (109, 179, 174),
        (175, 109, 179),
        (125, 25, 25),
        (21, 108, 21),
        (28, 44, 92),
        (181, 100, 20),
        (20, 181, 103),
        (138, 39, 189),
        (243, 142, 142),
        (130, 177, 99),
        (47, 116, 159),
        (132, 68, 45),
        (22, 91, 68),
        (147, 37, 112),
    ]

    def __init__(self, config_file):

        super().__init__()
        self.config_file = config_file
        self.show_meshes = True
        self.show_sulci = True
        self.twin_filters = {}
        self.cached_data = {}
        self.windows = {}
        self.twins = {}
        self.associations = {}
        self.used_colors = set()
        self.max_cache_subjects = 16

        self.read_config_file()

        main_w = Qt.QSplitter()
        self.setCentralWidget(main_w)
        control_panel = Qt.QWidget()
        main_w.addWidget(control_panel)
        self.control_panel = control_panel
        views = Qt.QWidget()
        main_w.addWidget(views)
        self.views = views
        self.build_control_panel()
        self.build_views()
        self.setAcceptDrops(True)

    def read_config_file(self):
        if self.config_file is None:
            self.config_file = osp.join(os.getcwd(), 'twin_config.json')
        config = {}
        try:
            with open(self.config_file) as f:
                config = json.load(f)
        except IOError:
            pass
        self.config = config
        self.dataset = config.get('dataset', {})
        self.twin_number = config.get('twin_number', 5)
        self.show_sulci = config.get('show_sulci', True)
        self.show_meshes = config.get('show_meshes', True)
        self.twin_filters = config.get('display_filter', {})
        for k, v in self.twin_filters.items():
            if not isinstance(v, list):
                self.twin_filters[k] = [v]
        side = self.dataset.get('metadata', {}).get('side')
        if side is not None:
            self.twin_filters['hémisphère'] = side
        self.max_cache_subjects = self.config.get('max_cache_subjects',
                                                  self.max_cache_subjects)

    def build_control_panel(self):
        mypath = osp.dirname(__file__)
        start_icn = Qt.QIcon(osp.join(mypath, 'restart.png'))
        asso_icn = Qt.QIcon(osp.join(mypath, 'link.png'))
        disso_icn = Qt.QIcon(osp.join(mypath, 'unlink.png'))
        unsel_icn = Qt.QIcon(osp.join(mypath, 'unselect.png'))
        verif_icn = Qt.QIcon(osp.join(mypath, 'reveal.png'))
        mesh_icn = Qt.QIcon(osp.join(mypath, 'meshes.png'))
        sulci_icn = Qt.QIcon(osp.join(mypath, 'sulci.png'))
        sync_icn = Qt.QIcon(osp.join(mypath, 'sync.png'))
        sett_icn = Qt.QIcon(osp.join(mypath, 'settings.png'))
        quit_icn = Qt.QIcon(osp.join(mypath, 'power.png'))

        vlay = Qt.QVBoxLayout()
        self.control_panel.setLayout(vlay)
        start_bt = Qt.QPushButton(start_icn, '')  # '↺ Démarrer'
        start_bt.setToolTip('↺ Redémarrer')
        vlay.addWidget(start_bt)
        asso_bt = Qt.QPushButton(asso_icn, '')
        asso_bt.setToolTip('Associer')
        vlay.addWidget(asso_bt)
        disso_bt = Qt.QPushButton(disso_icn, '')
        disso_bt.setToolTip('Dissocier')
        vlay.addWidget(disso_bt)
        unsel_bt = Qt.QPushButton(unsel_icn, '')
        unsel_bt.setToolTip('Dé-sélectionner')
        vlay.addWidget(unsel_bt)
        verif_bt = Qt.QPushButton(verif_icn, '')
        verif_bt.setToolTip('Révéler')
        vlay.addWidget(verif_bt)
        vlay.addStretch(1)
        mesh_bt = Qt.QPushButton(mesh_icn, '')
        mesh_bt.setToolTip('Voir / cacher les cerveaux')
        mesh_bt.setCheckable(True)
        mesh_bt.setChecked(self.show_meshes)
        vlay.addWidget(mesh_bt)
        sulci_bt = Qt.QPushButton(sulci_icn, '')
        sulci_bt.setToolTip('Voir / cacher les sillons')
        sulci_bt.setCheckable(True)
        sulci_bt.setChecked(self.show_sulci)
        vlay.addWidget(sulci_bt)
        sync_bt = Qt.QPushButton(sync_icn, '')
        sync_bt.setToolTip('Synchroniser les vues')
        vlay.addWidget(sync_bt)
        vlay.addStretch(1)
        sett_bt = Qt.QPushButton(sett_icn, '')
        sett_bt.setToolTip('Options...')
        vlay.addWidget(sett_bt)
        vlay.addStretch(1)
        quit_bt = Qt.QPushButton(quit_icn, '')  # '⏻ Quitter'
        vlay.addWidget(quit_bt)
        buttons = [start_bt, asso_bt, disso_bt, unsel_bt, verif_bt, mesh_bt,
                   sulci_bt, sync_bt, sett_bt, quit_bt]
        for button in buttons:
            button.setFixedHeight(64)
            button.setIconSize(Qt.QSize(48, 48))
        cw = self.control_panel.sizeHint().width()
        self.centralWidget().setSizes([cw, self.width() - cw])

        quit_bt.clicked.connect(self.close)
        start_bt.clicked.connect(self.start)
        asso_bt.clicked.connect(self.associate)
        disso_bt.clicked.connect(self.dissociate)
        unsel_bt.clicked.connect(self.unselect)
        verif_bt.clicked.connect(self.verify)
        mesh_bt.toggled.connect(self.display_meshes)
        sulci_bt.toggled.connect(self.display_sulci)
        sync_bt.clicked.connect(self.sync_views)
        sett_bt.clicked.connect(self.edit_settings)

    def get_metadata(self):
        meta = {
            'center': 'subjects',
            'acquisition': 'default_acquisition',
            'analysis': 'default_analysis',
            'side': self.side,
            'graph_version': '3.1',
            'sulci_recognition_session': '',
            'under_ses': '',
        }
        meta.update(self.dataset.get('metadata', {}))
        if meta['sulci_recognition_session'] != '':
            meta['under_ses'] = f'_{meta["sulci_recognition_session"]}'
        return meta

    def get_mesh(self, sub, force_load=True, get_filename=False):
        meta = self.get_metadata()
        meta['subject'] = sub
        datapath = '%(center)s/%(subject)s/t1mri/%(acquisition)s/%(analysis)s/segmentation/mesh/%(subject)s_%(side)shemi.gii' % meta
        mesh_f = osp.join(self.dataset.get('directory', ''), datapath)
        mesh = self.get_data(sub, mesh_f, force_load=force_load, with_trm=True)
        if get_filename:
            return (mesh, mesh_f)
        return mesh

    def get_graph(self, sub, force_load=True, get_filename=False):
        meta = self.get_metadata()
        meta['subject'] = sub
        datapath = '%(center)s/%(subject)s/t1mri/%(acquisition)s/%(analysis)s/folds/%(graph_version)s/%(sulci_recognition_session)s/%(side)s%(subject)s%(under_ses)s.arg' % meta
        graph_f = osp.join(self.dataset.get('directory', ''), datapath)
        graph = self.get_data(sub, graph_f, force_load=force_load)
        graph = self.cached_data.get(sub, {}).get(graph_f)
        if get_filename:
            return (graph, graph_f)
        return graph

    def get_data(self, sub, filename, force_load=True, with_trm=False):
        data = self.cached_data.get(sub, {}).get(filename)
        if data is None and force_load:
            a = ana.Anatomist('-b')
            data = a.loadObject(filename)
            if data is None:
                print('load data failed:', filename)
            trm = None
            if with_trm:
                meta = self.get_metadata()
                meta['subject'] = sub
                datapath = '%(center)s/%(subject)s/t1mri/%(acquisition)s/registration/RawT1-%(subject)s_%(acquisition)s_TO_Talairach-ACPC.trm' % meta
                trm_f = osp.join(self.dataset.get('directory', ''), datapath)
                if osp.exists(trm_f):
                    ref = a.createReferential()
                    a.loadTransformation(trm_f, ref, a.centralReferential())
                    data.setReferential(ref)
                    trm = True
            if not trm:
                data.loadReferentialFromHeader()
            self.cached_data.setdefault(sub, {})[filename] = data
            self.update_data_cache(sub)
        return data

    def update_data_cache(self, sub):
        # print('update_data_cache, cache:', len(self.cached_data), self.max_cache_subjects)
        if len(self.cached_data) > self.max_cache_subjects:
            ndel = len(self.cached_data) - self.max_cache_subjects
            i = 0
            for sub in list(self.cached_data.keys()):
                if sub not in self.windows:
                    # print('del cache for subject:', sub)
                    del self.cached_data[sub]
                    i += 1
                    if i == ndel:
                        break

    def columns(self):
        nt = np.min((self.twin_number, len(self.dataset['twins'])))
        ncol = int(np.ceil(np.sqrt(nt * 1.)))
        if ncol % 2 == 1:
            ncol += 1  # have even number of cols
        return ncol

    def build_views(self):
        glay = self.views.layout()
        if glay is None:
            glay = Qt.QGridLayout()
            self.views.setLayout(glay)
        a = ana.Anatomist('-b')
        twins = self.randomize()
        # print('twins:', twins)
        meta = self.get_metadata()

        ncol = self.columns()
        col = 0
        row = 0
        subjects = sum([self.dataset['twins'][tpair_name]
                        for tpair_name in twins], [])
        np.random.shuffle(subjects)
        # print('subjects:', subjects)

        for tpair_name in twins:
            tpair = self.dataset['twins'][tpair_name]
            for sub in tpair:
                self.twins[sub] = tpair_name

        check_icn = getattr(self, 'check_icon', None)
        if check_icn is None:
            mypath = osp.dirname(__file__)
            check_icn = Qt.QIcon(osp.join(mypath, 'link_light.png'))
            self.grip_pixmap = Qt.QPixmap(osp.join(mypath, 'grip.png'))

        for sub in subjects:
            meta['subject'] = sub
            if self.show_sulci:
                graph = self.get_graph(sub)
            if self.show_meshes:
                mesh = self.get_mesh(sub)

            wid = Qt.QWidget()
            lay = Qt.QHBoxLayout()
            wid.setLayout(lay)
            w = a.createWindow('3D', no_decoration=True, block=wid)
            lay.addWidget(w.internalRep.get())
            handle = DragFrame()
            handle.setObjectName(f'frame_{sub}')
            handle.setFrameShape(Qt.QFrame.Panel | Qt.QFrame.Raised)
            handle.setPixmap(self.grip_pixmap)
            handle.setFixedWidth(84)
            lay.addWidget(handle)
            objects = []
            if self.show_sulci:
                objects.append(graph)
            if self.show_meshes:
                objects.append(mesh)
            if objects:
                w.addObjects(objects)
            w.setHasCursor(False)
            w.setReferential(a.centralReferential())

            vlay = Qt.QVBoxLayout()
            handle.setLayout(vlay)
            check = Qt.QPushButton(check_icn, '')
            check.setIconSize(Qt.QSize(32, 32))
            check.setFixedSize(64, 64)
            check.setCheckable(True)
            vlay.addWidget(check)
            vlay.addStretch(1)
            self.views.layout().addWidget(wid, row, col)
            self.windows[sub] = (w, wid, row, col)
            col += 1
            if col == ncol:
                col = 0
                row += 1

    def randomize(self):
        nt = np.min((self.twin_number, len(self.dataset['twins'])))
        if nt == 0:
            self.displayed_twins = []
            return
        twin_list = set(self.dataset.get("twins", {}).keys())
        print('total twin pairs:', len(twin_list))
        twin_meta = self.dataset.get('twin_meta', {})
        meta_twins = {}  # the other way...
        # we need meta_key: value: [twin1, twin2...]
        for tn, meta in twin_meta.items():
            for k, v in meta.items():
                meta_twins.setdefault(k, {}).setdefault(v, []).append(tn)
        for k, vals in self.twin_filters.items():
            if k == 'hémisphère':
                continue
            filt = set()
            for v in vals:
                filt.update(meta_twins.get(k, {}).get(v, []))
            twin_list = twin_list.intersection(filt)
            print('filter:', k, v, '->', len(twin_list))
        side = self.twin_filters.get('hémisphère')
        if side is not None and len(side) == 1:
            sides = {'gauche': 'L', 'droit': 'R'}
            self.side = sides[side[0]]
        else:
            self.side = np.random.choice(['L', 'R'], 1, replace=False)[0]
        print('SIDE:', self.side)
        self.displayed_twins = np.random.choice(
            list(twin_list), nt, replace=False)
        return self.displayed_twins

    def views_order(self):
        ncol = self.columns()
        subjects = [None] * len(self.windows)
        for sub, view in self.windows.items():
            n = view[2] * ncol + view[3]
            subjects[n] = sub
        return subjects

    def reorder_views(self, subjects):
        ncol = self.columns()
        col = 0
        row = 0
        for sub in subjects:
            w, wid, r, c = self.windows[sub]
            self.views.layout().addWidget(wid, row, col)
            self.windows[sub] = (w, wid, row, col)
            col += 1
            if col == ncol:
                col = 0
                row += 1

    def close(self):
        if super().close():
            self.clear_all()
            Qt.QApplication.instance().quit()

    def clear_views(self):
        for sub, (w, wid, row, col) in self.windows.items():
            self.windows[sub] = None
            wid.layout().takeAt(1)
            wid.layout().takeAt(0)
            w.internalRep.setParent(None)
            del w
            wid.setParent(None)
            del wid
        self.windows = {}
        self.twins = {}
        self.associations = {}
        self.used_colors = set()
        ana.cpp.Referential.clearUnusedReferentials()

    def clear_all(self):
        self.clear_views()
        self.cached_data = {}

    def get_selection(self):
        sel = []
        for sub, (w, wid, row, col) in self.windows.items():
            frame = wid.layout().itemAt(1).widget()
            check_bt = frame.layout().itemAt(0).widget()
            if check_bt.isChecked():
                sel.append(sub)
        return sel

    def get_new_color(self):
        for i in range(len(self.colors_list)):
            if i not in self.used_colors:
                return (i, self.colors_list[i])

    def start(self):
        print('start')
        self.clear_views()
        self.build_views()

    def associate(self):
        sel = self.get_selection()
        if len(sel) != 2:
            print('Il faut sélectionner 2 sujets')
            return
        for sub in sel:
            if sub in self.associations:
                print(f'Le sujet {sub} est déjà associé à '
                      f'{self.associations[sub][0]}')
                return
        col_i, color = self.get_new_color()
        self.used_colors.add(col_i)
        self.associations[sel[0]] = (sel[1], col_i)
        self.associations[sel[1]] = (sel[0], col_i)
        f1 = self.windows[sel[0]][1].layout().itemAt(1).widget()
        f1.setStyleSheet(
            'QFrame#%s {background-color: rgb(%d, %d, %d);}'
            % (f1.objectName(), color[0], color[1], color[2]))
        f2 = self.windows[sel[1]][1].layout().itemAt(1).widget()
        f2.setStyleSheet(
            'QFrame#%s {background-color: rgb(%d, %d, %d);}'
            % (f2.objectName(), color[0], color[1], color[2]))
        self.unselect()
        subjects = self.views_order()
        i = subjects.index(sel[0])
        j = subjects.index(sel[1])
        if i < j:
            new_sub = subjects[:i+1] + [sel[1]] + \
                [s for s in subjects[i+1:] if s != sel[1]]
        else:
            new_sub = subjects[:j+1] + [sel[0]] + \
                [s for s in subjects[j+1:] if s != sel[0]]
        self.reorder_views(new_sub)

    def dissociate(self):
        sel = self.get_selection()
        for sub in sel:
            if sub not in self.associations:
                print(f'Le sujet {sub} n\'est pas associé.')
                continue
            other, col_i = self.associations[sub]
            del self.associations[sub]
            del self.associations[other]
            self.used_colors.remove(col_i)
            f1 = self.windows[sub][1].layout().itemAt(1).widget()
            f1.setStyleSheet('QFrame#%s {}' % f1.objectName())
            f2 = self.windows[other][1].layout().itemAt(1).widget()
            f2.setStyleSheet('QFrame#%s {}' % f2.objectName())
        self.unselect()

    def unselect(self):
        for sub, (w, wid, row, col) in self.windows.items():
            frame = wid.layout().itemAt(1).widget()
            check_bt = frame.layout().itemAt(0).widget()
            check_bt.setChecked(False)

    def verify(self):
        subjects = []
        col_i = 0
        colors = {}
        for sub, tpair_name in self.twins.items():
            color = colors.get(tpair_name)
            if color is not None:
                continue
            color = self.colors_list[col_i]
            col_i += 1
            colors[tpair_name] = color
            subs = self.dataset['twins'][tpair_name]
            subjects += subs
            for sub in subs:
                w, wid, row, col = self.windows[sub]
                lay = wid.layout().itemAt(1).widget().layout()
                if lay.itemAt(2) is not None:
                    continue
                frame = Qt.QFrame()
                frame.setFrameShape(Qt.QFrame.Panel | Qt.QFrame.Raised)
                frame.setFixedSize(36, 36)
                frame.setStyleSheet(
                    'QFrame {border-radius: 18px; '
                    'background-color: rgb(240, 240, 240)}')
                ly = Qt.QVBoxLayout()
                ly.setContentsMargins(0, 0, 0, 0)
                frame.setLayout(ly)
                label = Qt.QLabel()
                label.setObjectName(f'label_{sub}')
                label.setFrameShape(Qt.QFrame.Panel | Qt.QFrame.Raised)
                label.setStyleSheet(
                    'QLabel {background-color: rgb(%d, %d, %d); '
                    'border-radius: 16px}'
                    % (color[0], color[1], color[2]))
                label.setFixedSize(32, 32)
                ly.addWidget(label)
                ly.setAlignment(label, Qt.Qt.AlignCenter)
                lay.addWidget(frame)
                lay.setAlignment(frame, Qt.Qt.AlignCenter)
        self.reorder_views(subjects)

    def display_meshes(self, toggled):
        self.show_meshes = toggled
        for sub, (w, _, _, _) in self.windows.items():
            if toggled:
                mesh = self.get_mesh(sub, True)
                w.addObjects(mesh)
            else:
                mesh = self.get_mesh(sub, False)
                if mesh is not None:
                    w.removeObjects(mesh)

    def display_sulci(self, toggled):
        self.show_sulci = toggled
        a = ana.Anatomist('-b')
        for sub, (w, _, _, _) in self.windows.items():
            if toggled:
                graph = self.get_graph(sub, True)
                w.addObjects(graph)
            else:
                graph = self.get_graph(sub, False)
                if graph is not None:
                    # w.removeObjects(graph)
                    a.execute('RemoveObject', objects=[graph], windows=[w],
                              removechildren=1)

    def sync_views(self):
        source_view = None
        tosync = []
        for sub, (w, _, row, col) in self.windows.items():
            if row == 0 and col == 0:  # FIXME !
                source_view = w
            else:
                tosync.append(w)
        vinfo = source_view.getInfos()
        view_quat = vinfo['view_quaternion']
        slice_quat = vinfo['slice_quaternion']
        position = vinfo['position']
        obs_position = vinfo['observer_position']
        #bbmin = vinfo['boundingbox_min']
        zoom = vinfo['zoom']
        for w in tosync:
            w.camera(view_quaternion=view_quat,
                     slice_quaternion=slice_quat,
                     zoom=zoom,
                     cursor_position=position,
                     observer_position=obs_position)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        widget = e.source()

        child = self.childAt(pos)
        if child is None:
            e.ignore()
            return

        wids = {w: sub for sub, (_, w, _, _) in self.windows.items()}

        source = widget
        if source not in wids:
            source = source.parent()
            while source is not None:
                if source in wids:
                    break
                source = source.parent()
            else:
                e.ignore()
                return
        source_sub = wids[source]

        if child not in wids:
            child = child.parent()
            while child is not None:
                if child in wids:
                    break
                child = child.parent()
            else:
                e.ignore()
                return

        sub = wids[child]
        if sub == source_sub:
            e.ignore()
            return

        subjects = [s for s in self.views_order() if s != source_sub]
        i = subjects.index(sub)
        new_subjects = subjects[:i] + [source_sub] + subjects[i:]
        self.reorder_views(new_subjects)

        e.accept()

    def edit_settings(self):
        wid = Qt.QDialog(self)
        vl = Qt.QVBoxLayout()
        wid.setLayout(vl)

        hl1 = Qt.QHBoxLayout()
        vl.addLayout(hl1)
        hl1.addWidget(Qt.QLabel('Nombre de paires affichées:'))
        sb = Qt.QSpinBox()
        sb.setValue(self.twin_number)
        hl1.addWidget(sb)

        fb = Qt.QGroupBox('Filtres:')
        nc = 2
        fbl = Qt.QGridLayout()
        fb.setLayout(fbl)
        meta_set = {}
        for meta in self.dataset.get('twin_meta', {}).values():
            for k, v in meta.items():
                meta_set.setdefault(k, set()).add(v)
        meta_set['hémisphère'] = ['gauche', 'droit']
        row = 0
        col = 0
        filt_wids = {}
        for k, v in meta_set.items():
            hl = Qt.QHBoxLayout()
            fbl.addLayout(hl, row, col)
            hl.addWidget(Qt.QLabel(f'{k}:'))
            df = self.twin_filters.get(k)
            if True:
                vgb = Qt.QGroupBox()
                hl.addWidget(vgb)
                vl2 = Qt.QVBoxLayout()
                vbg = Qt.QButtonGroup(vgb)
                filt_wids[k] = (vbg, v)
                vbg.setExclusive(False)
                vgb.setLayout(vl2)
                for i, x in enumerate(v):
                    b = Qt.QCheckBox(str(x))
                    b.setChecked(df is None or x in df)
                    vl2.addWidget(b)
                    vbg.addButton(b, i)
            col += 1
            if col == nc:
                col = 0
                row += 1

        vl.addWidget(fb)

        vl.addStretch(1)
        hl = Qt.QHBoxLayout()
        vl.addLayout(hl)
        hl.addStretch(1)
        ok = Qt.QPushButton('OK')
        hl.addWidget(ok)
        can = Qt.QPushButton('Annuler')
        hl.addWidget(can)
        ok.clicked.connect(wid.accept)
        can.clicked.connect(wid.reject)

        res = wid.exec()
        if res == Qt.QDialog.Accepted:
            self.twin_number = sb.value()
            print('update filters')
            for k, fw in filt_wids.items():
                w, values = fw
                if isinstance(w, Qt.QButtonGroup):
                    vals = []
                    for v, b in zip(values, w.buttons()):
                        if b.isChecked():
                            vals.append(v)
                    if len(vals) == 0:
                        if k in self.twin_filters:
                            del self.twin_filters[k]
                    else:
                        self.twin_filters[k] = vals
            self.start()


def twin_game(config_file):

    qapp = Qt.QApplication([])
    tg = TwinGame(config_file)
    tg.showMaximized()
    qapp.exec()


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Twins Game')
    parser.add_argument('-c', '--config', type=str,
                        help='input JSON configuration file describing the '
                        'dataset and settings')

    options = parser.parse_args()
    print(options)
    config_file = options.config

    twin_game(config_file)
